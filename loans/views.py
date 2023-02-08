from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, render, resolve_url
from django.views.generic import TemplateView

from accounts.models import Member
from .models import LoanRequest


# Create your views here.
class LoanListView(LoginRequiredMixin, TemplateView):
    def get(self, request, context: str, *args, **kwargs):
        if context not in ("disbursed", "terminated"):
            raise Http404
        context = {
            "dashboard": {
                "title": "Loans",
                "context": "loans",
                "sub_context": context,
                "buttons": [
                    {
                        "title": "Repay Loan",
                        "class": "btn-primary-outline",
                        "url": resolve_url("dashboard:loans.repay"),
                    },
                    {
                        "target": "#nlrm",
                        "class": "btn-primary",
                        "title": "Request Loan",
                    },
                ],
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class MemberLoanListView(LoanListView):
    def get(self, request, member_id: int, *args, **kwargs):
        if context != "terminated":
            raise Http404
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "loans",
                "sub_context": "terminated",
                "title": "{} Terminated Loans".format(member.name),
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class LoanView(LoanListView):
    def get(self, request, loan_id: int, *args, **kwargs):
        if context != "terminated":
            raise Http404
        loan = get_object_or_404(LoanRequest, id=loan_id)
        context = {
            "loan": loan,
            "dashboard": {"context": "loans", "title": "Loan Repayments"},
        }
        template = f"accounts/pages/member.html"
        return render(request, template, context)
