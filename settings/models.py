from django.db import models

from cedar.constants import MONTH_CHOICES


# Create your models here.
class AccountChoice(models.Model):
    name = models.CharField(max_length=50)

    lir = models.FloatField("Loan Interest Percentage")
    sir = models.FloatField("Savings Interest Percentage", default=4)
    lsr = models.FloatField("Loan Savings Percentage", default=10)
    ld = models.IntegerField("Loan Duration", default=6)
    psisd = models.IntegerField("Pre-Savings Interest Start Duration", default=3)
    aad = models.IntegerField("Account Activity Duration", default=6)

    created_at = models.DateTimeField(auto_now_add=True)


class BusinessYear(models.Model):
    start_day = models.IntegerField("Starting Day of Business Year", default=1)
    start_month = models.IntegerField(
        "Starting Month of Business Year", default=4, choices=MONTH_CHOICES
    )
    end_day = models.IntegerField("Ending Day of Business Year", default=31)
    end_month = models.IntegerField(
        "Ending Month of Business Year", default=3, choices=MONTH_CHOICES
    )
