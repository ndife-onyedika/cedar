from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, render, resolve_url
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from notifications.signals import notify

from accounts.models import Member, User
from cedar.mixins import (
    display_duration,
    display_rate,
    get_amount,
    get_data_equivalent,
    get_daycount_nextdate,
)
from loans.forms import LoanRepaymentForm, LoanRequestForm

from .models import LoanRepayment, LoanRequest


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
                        "target": "#lrc",
                        "title": "Repay Loan",
                        "class": "btn-outline-primary",
                    },
                    {"target": "#lc", "class": "btn-primary", "title": "Request Loan"},
                ],
            },
        }
        template = f"dashboard/pages/index.html"
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        code = 400
        data = None
        message = None
        status = "error"
        form = LoanRequestForm(data=request.POST)
        if form.is_valid():
            code = 200
            status = "success"
            loan_request = form.save()
            message = "Transaction recorded successfully"
            notify.send(
                User.objects.get(is_superuser=True),
                level="success",
                recipient=User.objects.exclude(is_superuser=False),
                verb="Loan: Disbursed - {}".format(loan_request.member.name),
                description="{}'s loan request of {} has been disbursed.".format(
                    loan_request.member.name, get_amount(loan_request.amount)
                ),
            )
        else:
            data = {
                field: error[0]["message"]
                for field, error in form.errors.get_json_data(escape_html=True).items()
            }
        return code, status, message, data


class LoanOverview(LoginRequiredMixin, TemplateView):
    def get(self, request, loan_id: int, *args, **kwargs):
        loan = get_object_or_404(LoanRequest, id=loan_id)
        context = {
            "loan_id": loan.id,
            "lrf": LoanRepaymentForm(initial={"loan": loan}),
            "dashboard": {
                "back": True,
                "context": "loans",
                "title": "Loan Overview",
                "buttons": [
                    {
                        "target": "#lrc",
                        "title": "Repay Loan",
                        "class": "btn-primary",
                    }
                ]
                if loan.status == "disbursed"
                else [],
            },
        }

        context["data"] = [
            {"title": "Status", "detail": get_data_equivalent(loan.status, "lsc")},
            {"title": "Member", "detail": loan.member.name},
            {"title": "Amount", "detail": get_amount(amount=loan.amount)},
            {
                "title": "Outstanding Amount",
                "detail": get_amount(amount=loan.outstanding_amount),
            },
            {
                "title": "Guarantors",
                "detail": ", ".join(
                    [guarantor.name for guarantor in loan.guarantors.all()]
                )
                if loan.guarantors.all().count() > 0
                else "N/A",
            },
            {"title": "Interest Rate", "detail": display_rate(loan.interest_rate)},
            {"title": "Tenor", "detail": display_duration(loan.duration)},
            {"title": "Date Created", "detail": loan.created_at or "N/A"},
            {
                "title": "Date Terminated",
                "detail": loan.terminated_at or "Not Terminated",
            },
        ]

        template = f"dashboard/pages/views/analysis.html"
        return render(request, template, context)


class LoanView(LoginRequiredMixin, TemplateView):
    def getLoan(self, loan_id):
        loan = None
        try:
            loan = LoanRequest.objects.get(id=loan_id)
        except LoanRequest.DoesNotExist:
            code = 404
            status = "error"
            message = "Not Found"
        else:
            code = 200
            status = "success"
            message = "Record fetched"
        return code, status, message, loan

    def get(self, request, id, *args, **kwargs):
        data = {}
        code, status, message, loan = self.getLoan(id)
        if loan:
            data = {
                "member": loan.member.id,
                "amount": loan.amount / 100,
                "guarantors": [guarantor.id for guarantor in loan.guarantors.all()],
                "created_at": loan.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if loan.created_at
                else "",
            }
        return code, status, message, data

    def post(self, request, id, *args, **kwargs):
        data = {}
        code, status, message, loan = self.getLoan(id)
        if loan:
            form = LoanRequestForm(instance=loan, data=request.POST)
            print(form.errors)
            if form.is_valid():
                loan = form.save()
                message = "Transaction updated successfully"
            else:
                code = 400
                message = None
                status = "error"
                data = {
                    field: error[0]["message"]
                    for field, error in form.errors.get_json_data(
                        escape_html=True
                    ).items()
                }
        return code, status, message, data


class LoanRepaymentView(LoginRequiredMixin, TemplateView):
    def getRepay(self, repay_id):
        repay = None
        try:
            repay = LoanRepayment.objects.get(id=repay_id)
        except LoanRepayment.DoesNotExist:
            code = 404
            status = "error"
            message = "Not Found"
        else:
            code = 200
            status = "success"
            message = "Record fetched"
        return code, status, message, repay

    def get(self, request, id, *args, **kwargs):
        code, status, message, repay = self.getRepay(id)
        data = {}
        if repay:
            data = {
                "member": repay.member.id,
                "amount": repay.amount / 100,
                "created_at": repay.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                # "guarantors": [guarantor.id for guarantor in loan.guarantors.all()],
            }
        return code, status, message, data

    def post(self, request, id, *args, **kwargs):
        code, status, message, repay = self.getRepay(id)
        data = {}
        if repay:
            form = LoanRepaymentForm(instance=repay, data=request.POST)
            if form.is_valid():
                repay = form.save()
                message = "Transaction updated successfully"
            else:
                data = {
                    field: error[0]["message"]
                    for field, error in form.errors.get_json_data(
                        escape_html=True
                    ).items()
                }
        return code, status, message, data


def loan_repayment_view(request, *args, **kwargs):
    code = 400
    data = None
    message = None
    status = "error"
    form = LoanRepaymentForm(data=request.POST)
    print(form.errors)
    if form.is_valid():
        code = 200
        status = "success"
        loan_repayment = form.save()
        message = "Transaction recorded successfully"
        notify.send(
            User.objects.get(is_superuser=True),
            level="success",
            recipient=User.objects.exclude(is_superuser=False),
            verb="Loan: Repayment - {}".format(loan_repayment.member.name),
            description="{}'s loan repayment of {} has been recorded. Outstanding Amount: {}".format(
                loan_repayment.member.name,
                get_amount(loan_repayment.amount),
                get_amount(loan_repayment.loan.outstanding_amount)
                if hasattr(loan_repayment, "loan")
                else "",
            ),
        )
    else:
        data = {
            field: error[0]["message"]
            for field, error in form.errors.get_json_data(escape_html=True).items()
        }
    return code, status, message, data
