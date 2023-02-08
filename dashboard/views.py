from django.shortcuts import render, resolve_url
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import Member

from cedar.mixins import get_amount, get_data_equivalent
from savings.models import SavingsTotal, SavingsCredit, SavingsDebit
from django.db.models.aggregates import Sum
from loans.models import LoanRequest


# Create your views here.
class Dashboard(LoginRequiredMixin, TemplateView):
    """docstring for Dashboard."""

    def get(self, request, *args, **kwargs):
        context = {
            "savings": {},
            "service": {},
            "dashboard": {
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

        # WALLET
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
            }
            for txn in savings_credit.union(savings_debit).order_by("-created_at")
        ]
        context["service"] = [
            {"title": "Total Members Registered", "detail": Member.objects.count()},
            {
                "title": "Total Loan Disbursed",
                "detail": get_amount(
                    LoanRequest.objects.all().aggregate(Sum("amount"))["amount__sum"]
                    or 0
                ),
            },
            {
                "title": "Total Savings Deposited",
                "detail": get_amount(
                    savings_credit.filter(reason="credit-deposit").aggregate(
                        Sum("amount")
                    )["amount__sum"]
                    or 0
                ),
            },
            {
                "title": "Total Savings Withdran",
                "detail": get_amount(
                    savings_debit.filter(reason="debit-withdrawal").aggregate(
                        Sum("amount")
                    )["amount__sum"]
                    or 0
                ),
            },
        ]

        return render(request, "dashboard/pages/home.html", context)


class Profile(CustomLoginRequiredMixin, TemplateView):
    """Profile"""

    def get(self, request, slug, *args, **kwargs):
        context = {
            "main": {
                "title": _("Settings"),
            },
        }

        if slug == "profile":
            member = request.user.member
            template = "dashboard/pages/settings/edit_profile.html"
            context["form"] = UpdateUPDForm(instance=member, initial={"member": member})
            nok_instance, created = NextOfKin.objects.get_or_create(owner=member)
            context["nok_form"] = UpdateUNKForm(instance=nok_instance)
            context["sub_title"] = "Edit Profile"
            context["member_positions"] = get_member_positions(member=member)
        elif slug == "preference":
            template = "dashboard/pages/settings/preference.html"
            context["sub_title"] = "Preferences"

        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        """Handles Profile Details Update"""
        form = UpdateUPDForm(request.POST, instance=request.user.member)
        if form.is_valid():
            member = form.save(commit=False)
            member.user.name = form.cleaned_data["name"]
            member.user.email = form.cleaned_data["email"]
            member.user.save()
            member.save()

            flash_messages.info(request, _("Profile updated"))
        else:
            flash_messages.error(request, _("Profile cannot be updated"))

        return redirect(
            reverse(
                "dashboard:settings",
                kwargs={"slug": "profile"},
            )
        )
