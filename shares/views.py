from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView
from notifications.signals import notify

from accounts.models import Member, User
from cedar.mixins import get_amount, get_shares_total
from shares.forms import ShareAddForm
from shares.models import Shares, SharesTotal


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
        form = ShareAddForm(data=request.POST)
        isMember = request.POST.get("isMember", "").lower() == "true"
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
                    Q(member=share.member) if isMember else Q()
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


class ShareView(LoginRequiredMixin, TemplateView):
    def getShare(self, share_id):
        share = None
        try:
            share = Shares.objects.get(id=share_id)
        except Shares.DoesNotExist:
            code = 404
            status = "error"
            message = "Not Found"
        else:
            code = 200
            status = "success"
            message = "Record fetched"
        return code, status, message, share

    def get(self, request, id, *args, **kwargs):
        code, status, message, share = self.getShare(id)
        data = {}
        if share:
            data = {
                "member": share.member.id,
                "amount": share.amount / 100,
                "created_at": share.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        return code, status, message, data

    def post(self, request, id, *args, **kwargs):
        code, status, message, share = self.getShare(id)
        data = {}
        if share:
            form = ShareAddForm(instance=share, data=request.POST)
            isMember = request.POST.get("isMember", "").lower() == "true"
            if form.is_valid():
                share = form.save()
                message = "Transaction updated successfully"
                total_shares = (
                    SharesTotal.objects.filter(
                        Q(member=share.member) if isMember else Q()
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
                    for field, error in form.errors.get_json_data(
                        escape_html=True
                    ).items()
                }
        return code, status, message, data
