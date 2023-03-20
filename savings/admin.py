from django.contrib import admin

from cedar.admin import CustomAdmin
from cedar.mixins import get_amount, format_date_model
from .models import (
    SavingsCredit,
    SavingsDebit,
    SavingsInterest,
    SavingsInterestTotal,
    SavingsTotal,
    YearEndBalance,
)
from django.shortcuts import reverse
from django.utils.http import urlencode
from django.utils.html import format_html


# Register your models here.
@admin.register(SavingsCredit)
class SavingsCreditAdmin(CustomAdmin):
    list_display = ("member", "view_amount", "reason", "created_at")
    list_display_links = ("member",)

    search_fields = ("member__name", "member__email")
    ordering = ("-created_at",)
    list_filter = (
        # "amount",
        "reason",
        "created_at",
    )
    autocomplete_fields = ["member"]

    def view_amount(self, obj):
        return get_amount(obj.amount)

    view_amount.short_description = "Amount"


@admin.register(SavingsDebit)
class SavingsDebitAdmin(CustomAdmin):
    list_display = ("member", "view_amount", "reason", "created_at")
    list_display_links = ("member",)

    search_fields = ("member__name", "member__email")
    ordering = ("-created_at",)
    list_filter = ("reason", "created_at")
    autocomplete_fields = ["member"]

    def view_amount(self, obj):
        return get_amount(obj.amount)

    view_amount.short_description = "Amount"


@admin.register(SavingsTotal)
class SavingsTotalAdmin(CustomAdmin):
    list_display = ("member", "view_amount", "created_at", "updated_at")
    list_display_links = ("member",)

    search_fields = ("member__name", "member__email")
    ordering = ("member__name",)
    list_filter = (
        # "amount",
        "created_at",
        "updated_at",
    )
    autocomplete_fields = ["member"]

    def view_amount(self, obj):
        return get_amount(obj.amount)

    view_amount.short_description = "Amount"


@admin.register(SavingsInterest)
class SavingsInterestAdmin(CustomAdmin):
    list_display = (
        "member",
        "view_savings",
        "view_amount",
        "view_interest",
        "view_interest_total",
        "created_at",
    )
    list_display_links = ("member",)

    search_fields = ("member__name", "member__email")
    ordering = ("member__name", "-created_at")
    autocomplete_fields = ["member"]
    list_filter = (
        # "amount",
        "created_at",
    )

    def view_amount(self, obj):
        return get_amount(obj.amount)

    view_amount.short_description = "Amount"

    def view_interest(self, obj):
        return get_amount(obj.interest)

    view_interest.short_description = "Interest"

    def view_interest_total(self, obj):
        return get_amount(obj.total_interest)

    view_interest_total.short_description = "Total Interest"

    def view_savings(self, obj):
        # count = obj.person_set.count()
        url = (
            reverse(f"admin:savings_savingscredit_changelist")
            + "?"
            + urlencode({"id": f"{obj.savings.id}"})
        )
        return format_html(
            '<a href="{}">({}, {})</a>'.format(
                url,
                get_amount(obj.savings.amount),
                format_date_model(obj.savings.created_at),
            )
        )

    view_savings.short_description = "Savings"


@admin.register(SavingsInterestTotal)
class SavingsInterestTotalAdmin(CustomAdmin):
    list_display = (
        "member",
        "view_savings",
        "view_amount",
        "view_interest",
        "is_comp",
        "start_comp",
        "disabled",
        "created_at",
        "updated_at",
    )
    list_display_links = ("member",)

    search_fields = ("member__name", "member__email")
    ordering = ("member__name", "-created_at")
    autocomplete_fields = ["member"]
    list_filter = (
        # "amount",
        "is_comp",
        "start_comp",
        "disabled",
        "created_at",
        "updated_at",
    )

    def view_amount(self, obj):
        return get_amount(obj.amount)

    view_amount.short_description = "Amount"

    def view_interest(self, obj):
        return get_amount(obj.interest)

    view_interest.short_description = "Interest"

    def view_savings(self, obj):
        # count = obj.person_set.count()
        url = (
            reverse(f"admin:savings_savingscredit_changelist")
            + "?"
            + urlencode({"id": f"{obj.savings.id}"})
        )
        return format_html(
            '<a href="{}">({}, {})</a>'.format(
                url,
                get_amount(obj.savings.amount),
                format_date_model(obj.savings.created_at),
            )
        )

    view_savings.short_description = "Savings"


@admin.register(YearEndBalance)
class YearEndBalanceAdmin(CustomAdmin):
    list_display = ("member", "view_amount", "created_at")
    ordering = ("-created_at",)
    search_fields = ("member__name", "member__email")  #
    list_filter = ("created_at",)

    def view_amount(self, obj):
        return get_amount(obj.amount)

    view_amount.short_description = "Amount"
