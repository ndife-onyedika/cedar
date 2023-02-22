from dashboard.forms import ServiceForm, _validate_amount
from .models import SavingsCredit, SavingsDebit
from django import forms


class BaseForm(ServiceForm):
    class Meta:
        fields = ["member", "amount"]


class SavingsCreditForm(BaseForm):
    class Meta(BaseForm.Meta):
        model = SavingsCredit


class SavingsDebitForm(BaseForm):
    class Meta(BaseForm.Meta):
        model = SavingsDebit
