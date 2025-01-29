from django.contrib import admin
from django.shortcuts import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from import_export.admin import ImportMixin

from cedar.admin import CustomAdmin, CustomImportExportAdmin
from savings.utils.resources import SavingsCreditResource, SavingsDebitResource
from utils.helpers import format_date_model, get_amount

from .models import (
    SavingsCredit,
    SavingsDebit,
    SavingsInterest,
    SavingsInterestTotal,
    SavingsTotal,
    YearEndBalance,
)


# Register your models here.
@admin.register(SavingsCredit)
class SavingsCreditAdmin(CustomImportExportAdmin, CustomAdmin):
    resource_class = SavingsCreditResource

    date_hierarchy = "created_at"
    autocomplete_fields = ["member"]

    ordering = ("-created_at",)
    list_display_links = ("member",)
    list_filter = ("reason", "created_at")
    search_fields = ("member__name", "member__email")
    list_display = ("member", "amount_display", "reason", "created_at")


@admin.register(SavingsDebit)
class SavingsDebitAdmin(CustomImportExportAdmin, CustomAdmin):
    resource_class = SavingsDebitResource

    date_hierarchy = "created_at"
    autocomplete_fields = ["member"]

    ordering = ("-created_at",)
    list_display_links = ("member",)
    list_filter = ("reason", "created_at")
    search_fields = ("member__name", "member__email")
    list_display = ("member", "amount_display", "reason", "created_at")


@admin.register(SavingsTotal)
class SavingsTotalAdmin(CustomAdmin):
    date_hierarchy = "created_at"
    autocomplete_fields = ["member"]

    ordering = ("member__name",)
    list_display_links = ("member",)
    list_filter = ("created_at", "updated_at")
    search_fields = ("member__name", "member__email")
    list_display = ("member", "amount_display", "created_at", "updated_at")


@admin.register(SavingsInterest)
class SavingsInterestAdmin(CustomAdmin):
    date_hierarchy = "created_at"
    autocomplete_fields = ["member"]

    list_display = (
        "member",
        "view_savings",
        "amount_display",
        "interest_display",
        "total_interest_display",
        "created_at",
    )
    list_filter = ("created_at",)
    list_display_links = ("member",)
    search_fields = ("member__name", "member__email")
    ordering = ("-created_at", "member__name", "-total_interest")

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
    date_hierarchy = "created_at"
    autocomplete_fields = ["member"]

    list_display = (
        "member",
        "view_savings",
        "amount_display",
        "interest_display",
        "is_comp",
        "start_comp",
        "disabled",
        "created_at",
        "updated_at",
    )
    list_display_links = ("member",)
    ordering = ("member__name", "-created_at")
    search_fields = ("member__name", "member__email")
    list_filter = ("is_comp", "start_comp", "disabled", "created_at", "updated_at")

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
    date_hierarchy = "created_at"

    ordering = ("-created_at",)
    list_filter = ("created_at",)
    search_fields = ("member__name", "member__email")  #
    list_display = ("member", "amount_display", "created_at")
