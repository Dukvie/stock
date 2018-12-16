from django.urls import path

from . import views

app_name = 'stock'
urlpatterns = [
    path('', views.TickerList.as_view(), name='ticker_list'),
    path('<str:ticker_pk>', views.ticker_prices, name='ticker_prices'),
    path('<str:ticker_pk>/analytics', views.ticker_analitycs, name='ticker_analytics'),
    path('<str:ticker_pk>/delta', views.ticker_delta, name='ticker_delta'),
    path('<str:ticker_pk>/insider', views.ticker_transactions, name='ticker_insider'),
    path('<str:ticker_pk>/insider/<slug>', views.ticker_transactions, name='ticker_insider'),
]
