from django.db import models

from utils.choices import MONTH_CHOICES


# Create your models here.
class AccountChoice(models.Model):
    name = models.CharField(max_length=50)

    lir = models.FloatField("Loan Interest Rate")
    sir = models.FloatField("Savings Interest Rate", default=4)
    lsr = models.FloatField("Loan Savings Rate", default=10)
    ld = models.IntegerField("Loan Duration", default=6)
    psisd = models.IntegerField("Pre-Savings Interest Start Duration", default=3)
    aad = models.IntegerField("Account Activity Duration", default=6)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} Member"

    class Meta:
        verbose_name_plural = "Account Types"


class BusinessYear(models.Model):
    start_day = models.IntegerField("Starting Day of Business Year", default=1)
    start_month = models.IntegerField(
        "Starting Month of Business Year", default=4, choices=MONTH_CHOICES
    )
    end_day = models.IntegerField("Ending Day of Business Year", default=31)
    end_month = models.IntegerField(
        "Ending Month of Business Year", default=3, choices=MONTH_CHOICES
    )

    class Meta:
        verbose_name_plural = "Business Year"
