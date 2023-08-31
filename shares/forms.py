from accounts.models import Member
from dashboard.forms import ServiceForm, _validate_amount
from .models import Shares


class ShareAddForm(ServiceForm):
    class Meta:
        model = Shares
        fields = ["member", "amount", "created_at"]
