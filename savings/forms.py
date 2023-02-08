from dashboard.forms import ServiceForm
from .models import SavingsCredit, SavingsDebit


class BaseForm(ServiceForm):
    class Meta:
        fields = ["member", "amount"]


class SavingsCreditForm(BaseForm):
    class Meta(BaseForm.Meta):
        model = SavingsCredit


class SavingsDebitForm(BaseForm):
    class Meta(BaseForm.Meta):
        model = SavingsDebit
