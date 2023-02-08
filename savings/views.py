from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from accounts.models import Member


# Create your views here.
class SavingsListView(LoginRequiredMixin, TemplateView):
    def get(self, request, context: str, *args, **kwargs):
        if context not in ("all", "credit", "debit"):
            raise Http404
        context = {
            "dashboard": {
                "title": "Savings",
                "context": "savings",
                "sub_context": context,
                "buttons": [
                    {
                        "target": "#swm",
                        "title": "Withdraw",
                        "class": "btn-primary-outline",
                    },
                    {"target": "#sdm", "title": "Deposit", "class": "btn-primary"},
                ],
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class MemberSavingsListView(LoginRequiredMixin, TemplateView):
    def get(self, request, context: str, member_id: int, *args, **kwargs):
        if context not in ("all", "credit", "debit"):
            raise Http404
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "savings",
                "sub_context": context,
                "title": "{} Savings {}".format(member.name, context.capitalize()),
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class SavingsInterestListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "dashboard": {
                "title": "Savings Interests",
                "context": "savings.interest",
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class MemberSavingsInterestsListView(LoginRequiredMixin, TemplateView):
    def get(self, request, context: str, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "sub_context": context,
                "context": "savings.interest",
                "title": "{} Savings Interests".format(member.name),
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class YearEndBalanceListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {"dashboard": {"context": "eoy", "title": "Year End Balance"}}
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class MemberYearEndBalancesListView(LoginRequiredMixin, TemplateView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "eoy",
                "title": "{} Year End Balance".format(member.name),
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)
