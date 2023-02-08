from django import forms
from accounts.models import Member
from dashboard.forms import ServiceForm
from loans.models import LoanRepayment, LoanRequest
from cedar.mixins import get_amount, format_date_model


class LoanRequestForm(ServiceForm):
    guarantor_1 = forms.ChoiceField(required=True, choices=[])
    guarantor_2 = forms.ChoiceField(required=True, choices=[])

    class Meta:
        model = LoanRequest
        fields = ["member", "amount", "guarantor_1", "guarantor_2"]

    def __init__(self, *args, **kwargs):
        members = Member.objects.all().order_by("name")
        member_list = [
            (
                member.id,
                "{} ({})".format(
                    member.name, "Active" if member.is_active else "Inactive"
                ),
            )
            for member in members
        ]
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.fields["member"].choices = member_list
        self.fields["guarantor_1"].choices = member_list
        self.fields["guarantor_2"].choices = member_list


class LoanRepaymentForm(ServiceForm):
    loan = forms.ChoiceField(choices=[], required=True)

    class Meta:
        model = LoanRepayment
        fields = ["member", "amount"]

    def __init__(self, *args, **kwargs):
        init_args = kwargs.get("initial")
        member = init_args.get("member")
        loan_list = [(None, "Select Loan")]

        _list = LoanRequest.objects.filter(member=member, status="disbursed")
        loan_list += [
            (
                loan.pk,
                "{} | {} | {}".format(
                    get_amount(amount=loan.amount),
                    loan.duration,
                    format_date_model(loan.created_at),
                ),
            )
            for loan in _list
        ]
        super(LoanRepaymentForm, self).__init__(*args, **kwargs)
        self.fields["loan"].choices = loan_list
