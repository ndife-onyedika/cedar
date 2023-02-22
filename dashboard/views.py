from django.shortcuts import render, resolve_url
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import Member

from cedar.mixins import get_amount, get_data_equivalent
from savings.models import SavingsTotal, SavingsCredit, SavingsDebit
from django.db.models.aggregates import Sum
from loans.models import LoanRequest
from savings.forms import SavingsCreditForm, SavingsDebitForm
from shares.models import SharesTotal
from settings.forms import AccountChoiceFormSet, BusinessYearForm


# Create your views here.
class Dashboard(LoginRequiredMixin, TemplateView):
    """docstring for Dashboard."""

    def get(self, request, *args, **kwargs):
        context = {
            "savings": {},
            "sdf": SavingsCreditForm(),
            "swf": SavingsDebitForm(),
            "dashboard": {
                "cards": [],
                "title": "Home",
                "context": "home",
                "buttons": [
                    {
                        "title": "Add Member",
                        "class": "btn-primary",
                        "url": resolve_url("dashboard:members.add"),
                    }
                ],
            },
        }
        total_savings = (
            SavingsTotal.objects.all().aggregate(Sum("amount"))["amount__sum"] or 0
        )
        savings_credit = SavingsCredit.objects.all()
        savings_debit = SavingsDebit.objects.all()
        last_credit = savings_credit.last()
        last_debit = savings_debit.last()

        total_shares = (
            SharesTotal.objects.all().aggregate(Sum("amount"))["amount__sum"] or 0
        )

        # WALLET
        context["shares"] = get_amount(amount=total_shares)
        context["savings"]["balance"] = get_amount(amount=total_savings)

        context["savings"]["credit_last"] = get_amount(
            amount=last_credit.amount if last_credit else 0,
        )
        context["savings"]["debit_last"] = get_amount(
            amount=last_debit.amount if last_debit else 0,
        )
        context["savings"]["txn"] = [
            {
                "amount": "{}{}".format(
                    "+" if txn.reason.startswith("credit-") else "-",
                    get_amount(txn.amount),
                ),
                "reason": get_data_equivalent(txn.reason, "src"),
                "timestamp": txn.created_at,
                "member": txn.member.name,
            }
            for txn in savings_credit.union(savings_debit).order_by("-created_at")[:10]
        ]

        context["dashboard"]["cards"] = [
            {
                "icon": "user-outline",
                "title": "Total Members Registered",
                "detail": Member.objects.count(),
            },
            {
                "icon": "loan-outline",
                "title": "Total Loan Disbursed",
                "detail": get_amount(
                    LoanRequest.objects.all().aggregate(Sum("amount"))["amount__sum"]
                    or 0
                ),
            },
            {
                "icon": "credit-outline",
                "title": "Total Savings Deposited",
                "detail": get_amount(
                    savings_credit.filter(reason="credit-deposit").aggregate(
                        Sum("amount")
                    )["amount__sum"]
                    or 0
                ),
            },
            {
                "icon": "debit-outline",
                "title": "Total Savings Withdrawn",
                "detail": get_amount(
                    savings_debit.filter(reason="debit-withdrawal").aggregate(
                        Sum("amount")
                    )["amount__sum"]
                    or 0
                ),
            },
        ]

        return render(request, "dashboard/pages/home.html", context)


class Settings(LoginRequiredMixin, TemplateView):
    """Profile"""

    def get(self, request, *args, **kwargs):
        context = {
            "dashboard": {"title": "Settings", "context": "settings"},
        }
        formset = AccountChoiceFormSet()
        context["formset"] = formset
        context["form"] = BusinessYearForm()
        template = "dashboard/pages/settings.html"
        return render(request, template, context)
