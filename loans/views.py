from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, render, resolve_url
from django.views.generic import TemplateView

from accounts.models import Member
from cedar.mixins import (
    get_amount,
    get_data_equivalent,
    display_duration,
    display_rate,
    get_daycount_nextdate,
)
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
            "dashboard": {
                "context": "loans",
                "sub_context": "loans.repay",
                "title": "Loan Details",
            },
        }

        approval_date = loan.created_at.date()

        init_date = approval_date + get_daycount_nextdate(
            month_count=0, date=approval_date
        )
        end_date = init_date + get_daycount_nextdate(
            date=init_date, month_count=loan.duration
        )

        context["data"] = [
            {"title": "Status", "detail": get_data_equivalent(loan.status, "lsc")},
            {"title": "Member", "detail": loan.member.name},
            {"title": "Amount", "detail": get_amount(amount=loan.amount)},
            {
                "title": "Outstanding Amount",
                "detail": get_amount(amount=loan.outstanding_amount),
            },
            {"title": "Guarantor 1", "detail": loan.guarantor_1.name},
            {"title": "Guarantor 2", "detail": loan.guarantor_2.name},
            {"title": "Interest Rate", "detail": display_rate(loan.interest_rate)},
            {"title": "Tenor", "detail": display_duration(loan.duration)},
            {"title": "Date Created", "detail": loan.created_at},
            {"title": "Date Terminated", "detail": loan.terminated_at},
        ]

        template = f"dashboard/pages/records.html"
        return render(request, template, context)
