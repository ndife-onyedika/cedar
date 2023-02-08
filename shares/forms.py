from dashboard.forms import ServiceForm
from .models import Shares


class ShareAddForm(ServiceForm):
    class Meta:
        model = Shares
        fields = ["member", "amount"]
