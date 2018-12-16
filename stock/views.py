from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.views.generic.list import ListView

from stock.models import Ticker
from stock.forms import AnalyticsForm, DeltaForm

from dateutil.relativedelta import relativedelta


class TickerList(ListView):
    model = Ticker
    ordering = 'pk'
    context_object_name = 'tickers'


def ticker_prices(request, ticker_pk, api=False):
    ticker = get_object_or_404(Ticker, pk=ticker_pk)
    need_date = timezone.now() - relativedelta(months=3)
    ticker_prices = ticker.prices.filter(date__gt=need_date)
    context = {}
    if api:
        context['ticker'] = ticker.pk
        context['ticker_prices'] = list(ticker_prices.values())
        return JsonResponse(context)
    context['ticker'] = ticker
    context['ticker_prices'] = ticker_prices
    context['analytics_form'] = AnalyticsForm()
    context['delta_form'] = DeltaForm()
    return render(request, 'stock/ticker_prices.html', context)


def ticker_transactions(request, ticker_pk, api=False, *args, **kwargs):
    ticker = get_object_or_404(Ticker, pk=ticker_pk)
    ticker_transactions = ticker.transactions.filter(insider__slug=kwargs['slug']) if 'slug' in kwargs else ticker.transactions.all()
    context = {}
    if api:
        context['ticker'] = ticker.pk
        context['ticker_transactions'] = list(ticker_transactions.values(
            'insider__name',
            'relation',
            'last_date',
            'transaction_type',
            'owner_type',
            'shares_traded',
            'last_price',
            'shares_held',
        ))
        return JsonResponse(context)
    if 'slug' in kwargs:
        context['is_insider_transactions'] = True
    context['ticker'] = ticker
    context['ticker_transactions'] = ticker_transactions
    return render(request, 'stock/ticker_transactions.html', context)


def ticker_analitycs(request, ticker_pk, api=False):
    ticker = get_object_or_404(Ticker, pk=ticker_pk)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    context = {
        'date_from': date_from,
        'date_to': date_to,
    }
    if not (date_from and date_to):
        return render(request, 'stock/ticker_analytics.html', context)
    start_date = ticker.prices.filter(date__lte=date_from).order_by('-date').first()
    end_date = ticker.prices.filter(date__lte=date_to).order_by('-date').first()
    if start_date and end_date:
        context['diff_open_price'] = start_date.open_price - end_date.open_price
        context['diff_high_price'] = start_date.high_price - end_date.high_price
        context['diff_low_price'] = start_date.low_price - end_date.low_price
        context['diff_close_price'] = start_date.close_price - end_date.close_price
    else:
        context['not_found'] = True
    if api:
        context['ticker'] = ticker.pk
        return JsonResponse(context)
    context['ticker'] = ticker
    context['form'] = AnalyticsForm(request.GET)
    return render(request, 'stock/ticker_analytics.html', context)


def ticker_delta(request, ticker_pk, api=False):
    ticker = get_object_or_404(Ticker, pk=ticker_pk)
    context = {}
    price_diff = request.GET.get('value', 1)
    price_type = request.GET.get('type')
    if price_type not in ['open', 'high', 'low', 'close']:
        context['not_found'] = True
        return JsonResponse(context) if api else render(request, 'stock/ticker_delta.html', context)
    price_type += '_price'
    s = (
        '''SELECT MAX(first_select.date) as first_date, second_date, 'Рост' as direction FROM (
             SELECT t1.date, t1.{price_type}, MIN(t2.date) as second_date
             FROM stock_tickerprice t1
             INNER JOIN stock_tickerprice t2
             ON (t2.{price_type} >= t1.{price_type} + {price_diff})
             AND t1.date < t2.date
             AND t1.ticker_id = t2.ticker_id
             WHERE t1.ticker_id = '{ticker_id}'
             GROUP BY t1.id ORDER BY t1.date) first_select
         GROUP BY second_date
         UNION
         SELECT MAX(second_select.date) as first_date, second_date, 'Падение' as direction FROM (
             SELECT t1.date, t1.{price_type}, MIN(t2.date) as second_date
             FROM stock_tickerprice t1
             INNER JOIN stock_tickerprice t2
             ON (t2.{price_type} <= t1.{price_type} - {price_diff})
             AND t1.date < t2.date
             AND t1.ticker_id = t2.ticker_id
             WHERE t1.ticker_id = '{ticker_id}'
             GROUP BY t1.id ORDER BY t1.date) second_select
             GROUP BY second_date ORDER BY second_date;
        '''.format(ticker_id=ticker.pk,
                   price_diff=price_diff,
                   price_type=price_type,
                   )
    )
    cursor = connection.cursor()
    cursor.execute(s)
    results = cursor.fetchall()
    if api:
        context['ticker'] = ticker.pk
        context['results'] = list(results)
        return JsonResponse(context)
    context['form'] = DeltaForm(request.GET)
    context['results'] = results
    context['ticker'] = ticker
    return render(request, 'stock/ticker_delta.html', context)
