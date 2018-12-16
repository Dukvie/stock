from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Ticker(models.Model):
    name = models.CharField(
        verbose_name="Ticker name",
        max_length=5,
        primary_key=True,
    )

    def __str__(self):
        return self.name


class TickerPrice(models.Model):
    ticker = models.ForeignKey(
        Ticker,
        verbose_name="Ticker",
        related_name="prices",
        on_delete=models.CASCADE,
    )
    date = models.DateField(
        verbose_name="Date",
        default=timezone.now,
    )

    open_price = models.DecimalField(
        verbose_name="Open",
        max_digits=11,
        decimal_places=4,
    )
    high_price = models.DecimalField(
        verbose_name="High",
        max_digits=11,
        decimal_places=4,
    )
    low_price = models.DecimalField(
        verbose_name="Low",
        max_digits=11,
        decimal_places=4,
    )
    close_price = models.DecimalField(
        verbose_name="Close",
        max_digits=11,
        decimal_places=4,
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return '{} {}'.format(self.ticker, self.date.strftime('%d.%m.%Y'))


class Insider(models.Model):
    name = models.CharField(
        verbose_name="Name",
        max_length=128,
    )
    slug = models.SlugField(unique=True, max_length=140)

    def __str__(self):
        return self.name

    def generate_unique_slug(self):
        slug = slugify(self.name)
        gen_slug = slug
        num = 1
        while Insider.objects.filter(slug=gen_slug).exists():
            gen_slug = '{}-{}'.format(slug, num)
            num += 1
        return gen_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super(Insider, self).save(*args, **kwargs)


class Transaction(models.Model):
    insider = models.ForeignKey(
        Insider,
        verbose_name="Insider",
        related_name="transactions",
        on_delete=models.CASCADE,
    )
    ticker = models.ForeignKey(
        Ticker,
        verbose_name="Ticker",
        related_name="transactions",
        on_delete=models.CASCADE,
    )

    relation = models.CharField(
        verbose_name="Relation",
        max_length=64,
    )
    last_date = models.DateField(
        verbose_name="Last Date",
        default=timezone.now,
    )
    transaction_type = models.CharField(
        verbose_name="Transaction Type",
        max_length=128,
    )

    owner_type = models.CharField(
        verbose_name="OwnerType",
        max_length=32,
    )

    shares_traded = models.PositiveIntegerField(
        verbose_name="Shares Traded",
    )
    last_price = models.DecimalField(
        verbose_name="Last Price",
        max_digits=11,
        decimal_places=4,
        null=True,
        blank=True,
    )
    shares_held = models.PositiveIntegerField(
        verbose_name="Shares Held",
        default=0,
    )

    def __str__(self):
        return '{} {} {}'.format(self.last_date, self.insider, self.transaction_type)
