from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView
from notifications.signals import notify

from accounts.models import Member, User
from cedar.mixins import get_amount, get_shares_total
from shares.forms import ShareAddForm
from shares.models import SharesTotal


# Create your views here.
class ShareListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "asf": ShareAddForm(),
            "dashboard": {
                "title": "Shares",
                "context": "shares",
                "buttons": [
                    {"target": "#sc", "title": "Add Share", "class": "btn-primary"}
                ],
            },
        }
        total_shares = (
            SharesTotal.objects.all().aggregate(Sum("amount"))["amount__sum"] or 0
        )
        context["shares"] = get_amount(amount=total_shares)
        template = "dashboard/pages/index.html"
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        code = 400
        data = None
        message = None
        status = "error"
        isMember = request.POST.get("isMember").lower() == "true"
        form = ShareAddForm(data=request.POST)
        print(form.errors)
        if form.is_valid():
            code = 200
            status = "success"
            share = form.save()
            message = "Transaction recorded successfully"
            notify.send(
                User.objects.get(is_superuser=True),
                level="success",
                recipient=User.objects.exclude(is_superuser=False),
                verb="Shares: Share Added - {}".format(share.member.name),
                description="{}'s share of {} has been recorded. Total Shares: {}".format(
                    share.member.name,
                    get_amount(share.amount),
                    get_amount(get_shares_total(share.member)),
                ),
            )
            total_shares = (
                SharesTotal.objects.filter(
                    Q(member=share.member) if isMember else ()
                ).aggregate(Sum("amount"))["amount__sum"]
                or 0
            )
            data = {
                "id": share.id,
                "created_at": share.created_at,
                "total": get_amount(total_shares),
                "amount": get_amount(share.amount),
                "member": {"id": share.member.id, "name": share.member.name},
            }
        else:
            data = {
                field: error[0]["message"]
                for field, error in form.errors.get_json_data(escape_html=True).items()
            }
        return code, status, message, data


class MemberSharesListView(LoginRequiredMixin, TemplateView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "asf": ShareAddForm(),
            "dashboard": {
                "context": "shares",
                "title": "Shares - {}".format(member.name),
                "buttons": [
                    {
                        "target": "#asm",
                        "title": "Add Share",
                        "class": "btn-primary",
                    },
                ],
            },
        }
        template = f"dashboard/pages/index.html"
        return render(request, template, context)
