from django.db import models


class Exchange(models.TextChoices):
    OES = 'OES', 'OES'
    OTC = 'OTC', 'OTC'
    TSE = 'TSE', 'TSE'


class DayTrade(models.TextChoices):
    YES = 'Yes', 'Yes'
    NO = 'No', 'No'
    ONLY_BUY = 'OnlyBuy', 'Only Buy'


class Contract(models.Model):
    exchange = models.CharField(max_length=10, choices=Exchange.choices)
    code = models.CharField(max_length=50)
    symbol = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    unit = models.IntegerField()
    limit_up = models.FloatField()
    limit_down = models.FloatField()
    reference = models.FloatField()
    update_date = models.CharField(max_length=20)
    margin_trading_balance = models.IntegerField()
    short_selling_balance = models.IntegerField()
    day_trade = models.CharField(max_length=10, choices=DayTrade.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.name}"

    class Meta:
        db_table = 'contract'
