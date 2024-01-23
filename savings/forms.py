from django import forms

from dashboard.forms import ServiceForm, _validate_amount

from .models import SavingsCredit, SavingsDebit


class BaseForm(ServiceForm):
    class Meta(ServiceForm.Meta):
        pass


class SavingsCreditForm(BaseForm):
    class Meta(BaseForm.Meta):
        model = SavingsCredit


class SavingsDebitForm(BaseForm):
    class Meta(BaseForm.Meta):
        model = SavingsDebit
