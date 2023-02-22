from django import forms
from accounts.models import Member
from dashboard.forms import ServiceForm, _validate_amount
from loans.models import LoanRepayment, LoanRequest
from cedar.mixins import get_amount, format_date_model, get_member_choices


class LoanRequestForm(ServiceForm):
    class Meta:
        model = LoanRequest
        fields = ["member", "amount", "guarantor_1", "guarantor_2"]

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.fields["member"].choices = get_member_choices()
        self.fields["guarantor_1"].choices = get_member_choices()
        self.fields["guarantor_2"].choices = get_member_choices()

    def clean(self):
        data = self.cleaned_data
        data["amount"] = _validate_amount(amount=data.get("amount"))
        return data

    def save(self):
        data = self.cleaned_data
        member: Member = data.get("member")
        loan = LoanRequest.objects.create(
            member=member,
            amount=data.get("amount"),
            duration=member.account_type.ld,
            guarantor_1=data.get("guarantor_1"),
            guarantor_2=data.get("guarantor_2"),
            interest_rate=member.account_type.lir,
        )
        return loan


class LoanRepaymentForm(ServiceForm):
    class Meta:
        model = LoanRepayment
        fields = ["member", "amount"]

    def clean(self):
        data = self.cleaned_data
        data["amount"] = _validate_amount(amount=data.get("amount"))
        return data

    def save(self):
        data = self.cleaned_data
        member: Member = data.get("member")
        last_loan = LoanRequest.objects.get(member=member, status="disbursed")
        loan = LoanRepayment.objects.create(
            member=member,
            loan=last_loan,
            amount=data.get("amount"),
        )
        return loan
