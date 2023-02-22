from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, render, resolve_url
from django.views.generic import TemplateView

from accounts.models import Member
from loans.forms import LoanRepaymentForm, LoanRequestForm
from .models import LoanRequest


# Create your views here.
class LoanListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "lf": LoanRequestForm(),
            "lrf": LoanRepaymentForm(),
            "dashboard": {
                "title": "Loans",
                "context": "loans",
                "buttons": [
                    {
                        "target": "#lrm",
                        "title": "Repay Loan",
                        "class": "btn-outline-primary",
                    },
                    {
                        "target": "#lm",
                        "class": "btn-primary",
                        "title": "Request Loan",
                    },
                ],
            },
        }
        template = f"dashboard/pages/records.html"
        return render(request, template, context)


class MemberLoanListView(LoanListView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "loans",
                "sub_context": "terminated",
                "title": "Loans - {}".format(member.name),
            },
        }
        template = f"dashboard/pages/records.html"
        return render(request, template, context)


class LoanView(LoanListView):
    def get(self, request, loan_id: int, *args, **kwargs):
        loan = get_object_or_404(LoanRequest, id=loan_id)
        context = {
            "loan": loan,
            "dashboard": {"context": "loans", "title": "Loan Repayments"},
        }
        template = f"accounts/pages/member.html"
        return render(request, template, context)
