from django.contrib import admin
from cedar.admin import CustomAdmin
from cedar.mixins import display_duration, get_amount

from loans.models import LoanRequest


# Register your models here.
@admin.register(LoanRequest)
class LoanRequestAdmin(CustomAdmin):
    search_fields = ["loan__member__user__name", "loan__member__user__email"]

    list_display = (
        "member",
        "new_amount",
        "set_duration",
        "amount_outstanding",
        "status",
        "created_at",
    )
    list_display_links = ("member",)
    list_filter = ("status", "created_at")
    ordering = ("-created_at",)
    autocomplete_fields = ["member"]

    fieldsets = (
        (
            "Details",
            {
                "fields": (
                    "member",
                    "amount",
                    "duration",
                    "status",
                )
            },
        ),
        ("Guarantors", {"fields": ("guarantor_1", "guarantor_2")}),
        (
            "Calculation",
            {"fields": ("outstanding_amount",)},
        ),
        (
            "Advanced Options",
            {
                "classes": ("collapse",),
                "fields": ("terminated_at",),
            },
        ),
    )

    def new_amount(self, obj):
        return get_amount(amount=obj.amount)

    new_amount.short_description = "Amount Requested"

    def amount_outstanding(self, obj):
        return get_amount(amount=obj.outstanding_amount)

    def set_duration(self, obj):
        return display_duration(obj.duration)

    set_duration.short_description = "Tenor"
