from accounts.models import Member
from cedar.mixins import (
    get_amount,
    get_data_equivalent,
    display_duration,
    display_rate,
    format_date_model,
)
from dashboard.forms import ServiceForm
from loans.mixins import check_loan_eligibility
from loans.models import LoanRepayment, LoanRequest


class LoanRequestForm(ServiceForm):
    class Meta:
        model = LoanRequest
        fields = ["member", "amount", "guarantors", "created_at"]

    def __init__(self, *args, **kwargs):
        member = kwargs.get("initial", {}).get("member")
        super(LoanRequestForm, self).__init__(*args, **kwargs)
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

        if not self.instance and not member.is_active:
            self.add_error("member", "Member Inactive")

        if len(guarantors) > 2 or len(guarantors) < 2:
            self.add_error("guarantors", "Select only two guarantors")

        is_eligible = check_loan_eligibility(member, data["amount"])
        if not self.instance and not is_eligible:
            self.add_error(
                "amount",
                "Member does not have {}% of loan in savings.".format(
                    member.account_type.lsr
                ),
            )

        return data

    def save(self):
        data = self.cleaned_data
        print(data)
        print(self.instance)
        member = data.get("member")
        if self.instance:
            loan = self.instance
            loan.member = data.get("member", loan.member)
            loan.amount = data.get("amount", loan.amount)
            loan.save()
            [
                loan.guarantors.add(guarantor)
                for guarantor in data.get("guarantors", loan.guarantors.all())
            ]
        else:
            loan = LoanRequest(
                amount=data.get("amount"),
                member=data.get("member"),
                duration=member.account_type.ld,
                interest_rate=member.account_type.lir,
            )
            loan.save()
            [loan.guarantors.add(guarantor) for guarantor in data.get("guarantors")]

        return loan


class LoanRepaymentForm(ServiceForm):
    class Meta:
        model = LoanRepayment
        fields = ["member", "loan", "amount", "created_at"]

    def __init__(self, *args, **kwargs):
        loan = kwargs.get("initial", {}).get("loan")
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.fields["member"].choices = [(None, "Choose one")] + [
            (loan.member.id, loan.member.name)
            for loan in LoanRequest.objects.filter(status="disbursed").order_by(
                "member__name"
            )
        ]
        self.fields["loan"].choices = [(None, "Choose one")] + [
            (
                loan.id,
                "{} | {} | {} | {} | {}".format(
                    loan.member.name,
                    get_amount(loan.amount),
                    display_duration(loan.duration),
                    display_rate(loan.interest_rate),
                    format_date_model(loan.created_at),
                ),
            )
            for loan in LoanRequest.objects.filter(status="disbursed")
        ]
        if loan:
            self.fields["member"].disabled = True
            self.fields["member"].initial = loan.member
            self.fields["member"].widget.attrs = {"readonly": True}
            self.fields["loan"].disabled = True
            self.fields["loan"].initial = loan
            self.fields["loan"].widget.attrs = {"readonly": True}
