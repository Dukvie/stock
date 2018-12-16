from django import forms

from stock.models import TickerPrice


class AnalyticsForm(forms.Form):
    date_from = forms.DateField(
        label='с',
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
                'class': 'datepicker',
            }
        )
    )
    date_to = forms.DateField(
        label='до',
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
                'class': 'datepicker',
            }
        )
    )


class DeltaForm(forms.Form):
    value = forms.IntegerField(
        label='Значение',
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
            }
        )
    )
    price_types = [
        ('open', 'Цена открытия'),
        ('close', 'Цена закрытия'),
        ('high', 'Максимум'),
        ('low', 'Минимум'),
    ]
    type = forms.ChoiceField(label='Тип цены', choices=price_types)

    def __init__(self, *args, **kwargs):
        super(DeltaForm, self).__init__(*args, **kwargs)
