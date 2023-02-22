from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from accounts.models import Member
from savings.forms import SavingsCreditForm, SavingsDebitForm


# Create your views here.
class SavingsListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "sdf": SavingsCreditForm(),
            "swf": SavingsDebitForm(),
            "dashboard": {
                "title": "Savings",
                "context": "savings",
                "buttons": [
                    {
                        "target": "#swm",
                        "title": "Withdraw",
                        "class": "btn-outline-primary",
                    },
                    {"target": "#sdm", "title": "Deposit", "class": "btn-primary"},
                ],
            },
        }
        template = f"dashboard/pages/records.html"
        return render(request, template, context)


class MemberSavingsListView(LoginRequiredMixin, TemplateView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "savings",
                "title": "Savings - {}".format(member.name),
            },
        }
        template = "dashboard/pages/records.html"
        return render(request, template, context)


class SavingsInterestListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "dashboard": {
                "title": "Savings Interests",
                "context": "savings.interest",
            },
        }
        template = f"dashboard/pages/records.html"
        return render(request, template, context)


class MemberSavingsInterestsListView(LoginRequiredMixin, TemplateView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "savings.interest",
                "title": "Savings Interests - {}".format(member.name),
            },
        }
        template = f"dashboard/pages/records.html"
        return render(request, template, context)


class YearEndBalanceListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {"dashboard": {"context": "eoy", "title": "Year End Balance"}}
        template = f"dashboard/pages/records.html"
        return render(request, template, context)


class MemberYearEndBalancesListView(LoginRequiredMixin, TemplateView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "eoy",
                "title": "Year End Balance - {}".format(member.name),
            },
        }
        template = f"dashboard/pages/records.html"
        return render(request, template, context)
