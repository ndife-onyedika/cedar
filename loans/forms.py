from django import forms
from accounts.models import Member
from dashboard.forms import ServiceForm, _validate_amount
from loans.mixins import check_loan_eligibility
from loans.models import LoanRepayment, LoanRequest
from cedar.mixins import get_amount, format_date_model, get_member_choices


class LoanRequestForm(ServiceForm):
    class Meta:
        model = LoanRequest
        fields = ["member", "amount", "guarantors", "created_at"]

    def __init__(self, *args, **kwargs):
        super(LoanRequestForm, self).__init__(*args, **kwargs)
        member = kwargs.get("initial", {}).get("member")
        if member:
            self.fields["guarantors"].choices = [
                item
                for item in self.fields["guarantors"].choices
                if item[0] != member.id
            ]

    def clean(self):
        data = super(LoanRequestForm, self).clean()

        member = data["member"]
        guarantors = data["guarantors"]

        if not member.is_active:
            self.add_error("member", "Member Inactive")

        if len(guarantors) > 2:
            self.add_error("guarantors", "Select only two guarantors")

        is_eligible = check_loan_eligibility(member, data["amount"])
        if not is_eligible:
            self.add_error(
                "amount",
                "Member does not have {}% of loan in savings.".format(
                    member.account_type.lsr
                ),
            )

        return data

    def save(self):
        data = self.cleaned_data
        member: Member = data.get("member")
        loan = LoanRequest.objects.create(
            member=member,
            amount=data.get("amount"),
            duration=member.account_type.ld,
            interest_rate=member.account_type.lir,
        )
        [loan.guarantors.add(guarantor) for guarantor in data.get("guarantors")]
        return loan


class LoanRepaymentForm(ServiceForm):
    class Meta:
        model = LoanRepayment
        fields = ["member", "loan", "amount", "created_at"]

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.fields["member"].choices = [(None, "Select Member")] + [
            (loan.member.id, loan.member.name)
            for loan in LoanRequest.objects.filter(status="disbursed").order_by(
                "member__name"
            )
        ]

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
