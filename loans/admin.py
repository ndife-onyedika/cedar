from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from cedar.admin import CustomAdmin
from loans.models import LoanRepayment, LoanRequest
from utils.helpers import display_duration, display_rate, format_date_model, get_amount


# Register your models here.
@admin.register(LoanRequest)
class LoanRequestAdmin(CustomAdmin):
    autocomplete_fields = ["member"]
    search_fields = ["member__name", "member__email"]

    list_display = (
        "member",
        "amount_display",
        "set_duration",
        "amount_outstanding",
        "status",
        "created_at",
    )
    ordering = ("-created_at",)
    list_display_links = ("member",)
    list_filter = ("status", "created_at")

    fieldsets = (
        ("Details", {"fields": ("member", "amount", "duration", "status")}),
        ("Guarantors", {"fields": ("guarantors",)}),
        ("Calculation", {"fields": ("outstanding_amount",)}),
        ("Advanced Options", {"classes": ("collapse",), "fields": ("terminated_at",)}),
    )

    def amount_outstanding(self, obj):
        return get_amount(amount=obj.outstanding_amount)

    amount_outstanding.short_description = "Outstanding Amount"

    def set_duration(self, obj):
        return display_duration(obj.duration)

    set_duration.short_description = "Tenor"


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(CustomAdmin):
    search_fields = ["member__name", "member__email"]
    list_display = ("member", "view_loan", "view_amount", "created_at")
    ordering = ("-created_at",)
    autocomplete_fields = ["member"]

    def view_amount(self, obj):
        return get_amount(amount=obj.amount)

    view_amount.short_description = "Amount"

    def view_loan(self, obj):
        # count = obj.person_set.count()
        url = (
            reverse(f"admin:loans_loanrequest_changelist")
            + "?"
            + urlencode({"id": f"{obj.loan.id}"})
        )
        return format_html(
            '<a href="{}">({}, {}, {}, {})</a>'.format(
                url,
                get_amount(amount=obj.loan.amount),
                display_rate(obj.loan.interest_rate),
                display_duration(obj.loan.duration),
                format_date_model(obj.loan.created_at),
            )
        )

    view_loan.short_description = "Loan"
