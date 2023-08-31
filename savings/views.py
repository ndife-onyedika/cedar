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
from savings.models import SavingsCredit, SavingsDebit, SavingsTotal

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


class SavingsCreditView(LoginRequiredMixin, TemplateView):
    def getSavingsCredit(self, id):
        credit = None
        try:
            credit = SavingsCredit.objects.get(id=id)
        except SavingsCredit.DoesNotExist:
            code = 404
            status = "error"
            message = "Not Found"
        else:
            code = 200
            status = "success"
            message = "Record fetched"
        return code, status, message, credit

    def get(self, request, id, *args, **kwargs):
        code, status, message, credit = self.getSavingsCredit(id)
        data = {}
        if credit:
            data = {
                "reason": credit.reason,
                "member": credit.member.id,
                "amount": credit.amount / 100,
                "created_at": credit.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        return code, status, message, data

    def post(self, request, id, *args, **kwargs):
        code, status, message, credit = self.getSavingsCredit(id)
        data = {}
        if credit:
            form = SavingsCreditForm(instance=credit, data=request.POST)
            isMember = request.POST.get("isMember", "").lower() == "true"
            if form.is_valid():
                credit = form.save()
                message = "Transaction updated successfully"
                total_savings = (
                    SavingsTotal.objects.filter(
                        Q(member=credit.member) if isMember else Q()
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
                    for field, error in form.errors.get_json_data(
                        escape_html=True
                    ).items()
                }
        return code, status, message, data


class SavingsDebitView(LoginRequiredMixin, TemplateView):
    def getSavingsDebit(self, id):
        debit = None
        try:
            debit = SavingsDebit.objects.get(id=id)
        except SavingsDebit.DoesNotExist:
            code = 404
            status = "error"
            message = "Not Found"
        else:
            code = 200
            status = "success"
            message = "Record fetched"
        return code, status, message, debit

    def get(self, request, id, *args, **kwargs):
        code, status, message, debit = self.getSavingsDebit(id)
        data = {}
        if debit:
            data = {
                "reason": debit.reason,
                "member": debit.member.id,
                "amount": debit.amount / 100,
                "created_at": debit.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        return code, status, message, data

    def post(self, request, id, *args, **kwargs):
        code, status, message, debit = self.getSavingsDebit(id)
        data = {}
        if debit:
            form = SavingsCreditForm(instance=debit, data=request.POST)
            isMember = request.POST.get("isMember", "").lower() == "true"
            if form.is_valid():
                debit = form.save()
                message = "Transaction updated successfully"
                total_savings = (
                    SavingsTotal.objects.filter(
                        Q(member=debit.member) if isMember else Q()
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
                    for field, error in form.errors.get_json_data(
                        escape_html=True
                    ).items()
                }
        return code, status, message, data


def savings_credit_view(request, *args, **kwargs):
    code = 400
    data = None
    message = None
    status = "error"
    isMember = request.POST.get("isMember", "").lower() == "true"
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
                Q(member=credit.member) if isMember else Q()
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


def savings_debit_view(request, *args, **kwargs):
    code = 400
    data = None
    message = None
    status = "error"
    isMember = request.POST.get("isMember", "").lower() == "true"
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
                Q(member=debit.member) if isMember else Q()
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
