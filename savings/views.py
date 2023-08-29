from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.aggregates import Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from notifications.signals import notify

from accounts.models import Member, User
from cedar.mixins import get_amount, get_savings_total
from savings.forms import SavingsCreditForm, SavingsDebitForm
from savings.models import SavingsTotal

from django.db.models.query_utils import Q


# Create your views here.
class SavingsListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "swf": SavingsDebitForm(),
            "sdf": SavingsCreditForm(),
            "dashboard": {
                "title": "Savings",
                "context": "savings",
                "buttons": [
                    {
                        "target": "#swc",
                        "title": "Withdraw",
                        "class": "btn-outline-primary",
                    },
                    {"target": "#sdc", "title": "Deposit", "class": "btn-primary"},
                ],
            },
        }
        template = f"dashboard/pages/index.html"
        return render(request, template, context)


class SavingsInterestListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "dashboard": {"title": "Savings Interests", "context": "savings_interest"},
        }
        template = f"dashboard/pages/index.html"
        return render(request, template, context)


class YearEndBalanceListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {"dashboard": {"context": "eoy", "title": "Year End Balance"}}
        template = f"dashboard/pages/index.html"
        return render(request, template, context)


@login_required
@require_http_methods(["POST"])
def savings_credit_view(request, *args, **kwargs):
    code = 400
    data = None
    message = None
    status = "error"
    isMember = request.POST.get("isMember").lower() == "true"
    form = SavingsCreditForm(data=request.POST)
    print(form.errors)
    if form.is_valid():
        code = 200
        status = "success"
        credit = form.save()
        message = "Transaction recorded successfully"
        notify.send(
            User.objects.get(is_superuser=True),
            level="success",
            recipient=User.objects.exclude(is_superuser=False),
            verb="Savings: Credit - {}".format(credit.member.name),
            description="{}'s deposit of {} has been recorded. Total Savings: {}".format(
                credit.member.name,
                get_amount(credit.amount),
                get_amount(get_savings_total(credit.member).amount),
            ),
        )
        total_savings = (
            SavingsTotal.objects.filter(
                Q(member=credit.member) if isMember else ()
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        data = {
            "id": credit.id,
            "created_at": credit.created_at,
            "amount": get_amount(credit.amount),
            "total": get_amount(amount=total_savings),
            "member": {"id": credit.member.id, "name": credit.member.name},
        }
    else:
        data = {
            field: error[0]["message"]
            for field, error in form.errors.get_json_data(escape_html=True).items()
        }
    return code, status, message, data


@login_required
@require_http_methods(["POST"])
def savings_debit_view(request, *args, **kwargs):
    code = 400
    data = None
    message = None
    status = "error"
    isMember = request.POST.get("isMember").lower() == "true"
    form = SavingsDebitForm(data=request.POST)
    print(form.errors)
    if form.is_valid():
        code = 200
        status = "success"
        debit = form.save()
        message = "Transaction recorded successfully"
        notify.send(
            User.objects.get(is_superuser=True),
            level="success",
            recipient=User.objects.exclude(is_superuser=False),
            verb="Savings: Debit - {}".format(debit.member.name),
            description="{}'s withdrawal of {} has been recorded. Total Savings: {}".format(
                debit.member.name,
                get_amount(debit.amount),
                get_amount(get_savings_total(debit.member).amount),
            ),
        )

        total_savings = (
            SavingsTotal.objects.filter(
                Q(member=debit.member) if isMember else ()
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        data = {
            "id": debit.id,
            "created_at": debit.created_at,
            "amount": get_amount(debit.amount),
            "total": get_amount(amount=total_savings),
            "member": {"id": debit.member.id, "name": debit.member.name},
        }
    else:
        data = {
            field: error[0]["message"]
            for field, error in form.errors.get_json_data(escape_html=True).items()
        }
    return code, status, message, data
