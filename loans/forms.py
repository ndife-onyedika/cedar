from accounts.models import Member
from cedar.mixins import (
    display_duration,
    display_rate,
    format_date_model,
    get_amount,
    get_data_equivalent,
)
from dashboard.forms import ServiceForm
from loans.mixins import check_loan_eligibility
from loans.models import LoanRepayment, LoanRequest


class LoanRequestForm(ServiceForm):
    class Meta(ServiceForm.Meta):
        model = LoanRequest
        fields = ServiceForm.Meta.fields + ["guarantors"]

    def clean(self) -> dict:
        data = self.cleaned_data

        member = data["member"]
        guarantors = data["guarantors"]

        if not member.is_active:
            self.add_error("member", "Member Inactive")

        if len(guarantors) != 2:
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
        member = data.get("member")

        loan = LoanRequest(
            member=member,
            amount=data["amount"],
            duration=member.account_type.ld,
            interest_rate=member.account_type.lir,
        )
        loan.save()
        loan.guarantors.clear()
        [loan.guarantors.add(guarantor) for guarantor in data.get("guarantors")]

        return loan


class LoanRequestEditForm(ServiceForm):
    class Meta(ServiceForm.Meta):
        model = LoanRequest
        fields = ServiceForm.Meta.fields + ["guarantors"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = kwargs.get("instance")
        self.fields["guarantors"].choices = [
            item
            for item in self.fields["guarantors"].choices
            if item[0] != self.instance.member.id
        ]

    def clean(self) -> dict:
        data = self.cleaned_data
        guarantors = data["guarantors"]
        if len(guarantors) != 2:
            self.add_error("guarantors", "Select only two guarantors")

        return data

    def save(self):
        data = self.cleaned_data
        member = data.get("member")
        loan = self.instance
        loan.member = member
        loan.amount = data["amount"]
        loan.save()
        loan.guarantors.clear()
        [loan.guarantors.add(guarantor) for guarantor in data.get("guarantors")]

        return loan


class LoanRepaymentForm(ServiceForm):
    class Meta(ServiceForm.Meta):
        model = LoanRepayment
        fields = ServiceForm.Meta.fields + ["loan"]

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        initial = kwargs.get("initial", {})
        loan = initial.get("loan")

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
