from accounts.models import Member
from dashboard.forms import ServiceForm, _validate_amount
from .models import Shares


class ShareAddForm(ServiceForm):
    class Meta:
        model = Shares
        fields = ["member", "amount"]

    def clean(self):
        data = self.cleaned_data
        data["amount"] = _validate_amount(amount=data.get("amount"))
        return data

    def save(self):
        data = self.cleaned_data
        member: Member = data.get("member")
        shares = Shares.objects.create(member=member, amount=data.get("amount"))
        return shares
