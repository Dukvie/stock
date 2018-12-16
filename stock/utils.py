import requests
from bs4 import BeautifulSoup as bs
from multiprocessing import Pool

from django.utils import timezone

import django
django.setup()

from stock.models import Ticker, TickerPrice, Transaction, Insider


class Parser:

    def run_parse(self, ticker_data):
        ticker = ticker_data['ticker']
        if not Ticker.objects.filter(name=ticker).exists():
            Ticker.objects.create(name=ticker)
        html_page = requests.get(ticker_data['url']).text
        soup = bs(html_page, 'html.parser')
        if ticker_data['type'] == 'historical':
            return {
                'type': ticker_data['type'],
                'objects': self.parse_historical(ticker, soup),
            }
        elif ticker_data['type'] == 'insider-trades':
            return {
                'type': ticker_data['type'],
                'objects': self.parse_insider_trades(ticker, soup),
            }

    def parse(self, threads=1):
        tickers = self.get_tickers()
        if not tickers:
            raise ValueError('Файл tickers.txt не существует или является пустым')
        tickers_gen = self.get_tickers_generator(tickers)
        with Pool(threads) as pool:
            records = pool.map(self.run_parse, tickers_gen)
        price_objects = []
        transaction_objects = []
        for r in records:
            if r.get('type') == 'historical':
                price_objects += r['objects']
            else:
                transaction_objects += r['objects']
        TickerPrice.objects.bulk_create(price_objects)
        Transaction.objects.bulk_create(transaction_objects)

    def get_tickers(self):
        with open('tickers.txt', mode='r') as file:
            return [line.rstrip() for line in file]

    def get_tickers_generator(self, tickers):
        for ticker in tickers:
            yield dict(
                ticker=ticker,
                type='historical',
                url='https://www.nasdaq.com/symbol/{}/historical'.format(ticker.lower()),
            )

            for page in range(1, 11):
                yield dict(
                    ticker=ticker,
                    type='insider-trades',
                    url='https://www.nasdaq.com/symbol/{ticker}/insider-trades?page={page}'.format(ticker=ticker.lower(), page=page),
                )

    def date_serialize(self, date):
        if len(date) < 10:
            return timezone.now().strftime('%Y-%m-%d')
        split_date = [date_part for date_part in date.split('/')]
        return '{Y}-{m}-{d}'.format(Y=split_date[2], m=split_date[0], d=split_date[1])

    def parse_historical(self, ticker, soup):
        table_data = []
        div_with_table = soup.find('div', id='quotes_content_left_pnlAJAX')
        table_body = div_with_table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            cells = [cell.text.strip() for cell in cells]
            table_data.append(dict(
                date=self.date_serialize(cells[0]),
                open_price=cells[1],
                high_price=cells[2],
                low_price=cells[3],
                close_price=cells[4],
            ))
        return [TickerPrice(ticker_id=ticker, **data) for data in table_data]

    def parse_insider_trades(self, ticker, soup):
        table_data = []
        div_with_table = soup.find('div', {'class': 'genTable'})
        table = div_with_table.find('table')
        rows = table.find_all('tr')
        for row in rows[1:]:
            cells = row.find_all('td')
            cells = [cell.text.strip() for cell in cells]
            insider, create = Insider.objects.get_or_create(name=cells[0])
            table_data.append(dict(
                insider=insider,
                relation=cells[1],
                last_date=self.date_serialize(cells[2]),
                transaction_type=cells[3],
                owner_type=cells[4],
                shares_traded=cells[5].replace(',', ''),
                last_price=cells[6] if cells[6] else None,
                shares_held=cells[7].replace(',', ''),
            ))
        return [Transaction(ticker_id=ticker, **data) for data in table_data]
