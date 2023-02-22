import json
from django.contrib import messages as flash_messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.urls import reverse
from django.views.generic import TemplateView

from accounts.models import Member, NextOfKin
from cedar.decorators import redirect_authenticated
from cedar.mixins import (
    get_amount,
    get_savings_total,
    get_shares_total,
    get_data_equivalent,
)
from savings.forms import SavingsCreditForm, SavingsDebitForm
from savings.models import SavingsCredit, SavingsDebit, SavingsTotal
from settings.models import AccountChoice
from django.db.models.aggregates import Sum

from .forms import CustomPasswordResetForm, EditMemberForm, LoginForm, RegistrationForm


# Create your views here.
class MemberListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "mf": RegistrationForm(),
            "dashboard": {
                "title": "Members",
                "context": "members",
                "buttons": [
                    {
                        "target": "#mm",
                        "title": "Add Member",
                        "class": "btn-primary",
                    }
                ],
            },
        }
        template = f"dashboard/pages/records.html"
        return render(request, template, context)


class MemberView(MemberListView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "savings": {},
            "member": member,
            "sdf": SavingsCreditForm(),
            "swf": SavingsDebitForm(),
            "form": EditMemberForm(instance=member),
            "dashboard": {
                "context": "members",
                "title": "Member Details",
                "buttons": [
                    {"id": "editBtn", "title": "Edit", "class": "btn-primary"},
                    {
                        "id": "setBtn",
                        "target": "#cm",
                        "title": "Set {}".format(
                            "Active" if not member.is_active else "Inactive"
                        ),
                        "class": "btn-{}".format(
                            "primary" if not member.is_active else "danger"
                        ),
                        "value": json.dumps(
                            {
                                "id": [member.id],
                                "context": "status",
                                "value": "active"
                                if not member.is_active
                                else "inactive",
                            }
                        ),
                    },
                    {
                        "id": "delBtn",
                        "target": "#cm",
                        "title": "Delete",
                        "class": "btn-danger",
                        "value": json.dumps(
                            {
                                "id": [member.id],
                                "context": "delete",
                                "sub_context": "member",
                            }
                        ),
                    },
                ],
            },
        }
        total_savings = get_savings_total(member=member)
        savings_credit = SavingsCredit.objects.filter(member=member)
        savings_debit = SavingsDebit.objects.filter(member=member)
        last_credit = savings_credit.last()
        last_debit = savings_debit.last()
        total_shares = get_shares_total(member=member)
        context["shares"] = get_amount(amount=total_shares)
        context["savings"]["balance"] = get_amount(amount=total_savings)

        context["savings"]["credit_last"] = get_amount(
            amount=last_credit.amount if last_credit else 0,
        )
        context["savings"]["debit_last"] = get_amount(
            amount=last_debit.amount if last_debit else 0,
        )
        context["savings"]["txn"] = [
            {
                "amount": "{}{}".format(
                    "+" if txn.reason.startswith("credit-") else "-",
                    get_amount(txn.amount),
                ),
                "reason": get_data_equivalent(txn.reason, "src"),
                "timestamp": txn.created_at,
            }
            for txn in savings_credit.union(savings_debit).order_by("-created_at")[:10]
        ]
        template = f"accounts/member.html"
        return render(request, template, context)


@login_required
def registration_view(request):
    form = RegistrationForm(
        {}
        if request.method == "GET"
        else {"data": request.POST, "files": request.FILES}
    )
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                member = form.save(commit=False)
                member.account_type = AccountChoice.objects.get(
                    id=form.cleaned_data.get("account_type")
                )
                member.save()
                NextOfKin.objects.create(
                    member=member,
                    name=form.cleaned_data.get("nok_name"),
                    email=form.cleaned_data.get("nok_email"),
                    phone=form.cleaned_data.get("nok_phone"),
                    address=form.cleaned_data.get("nok_address"),
                    relationship=form.cleaned_data.get("nok_relationship"),
                )
        except IntegrityError as e:
            print(f"REGISTRATION-ERROR: {e}")
            flash_messages.error(request, "Error registering account")
        else:
            flash_messages.success(request, "Account registered successfully")
            return redirect("dashboard:members")
    return render(
        request, context={"form": form}, template_name="accounts/register.html"
    )


@redirect_authenticated(to_view_name="dashboard:home")
def login_view(request):
    attr = {} if request.method == "GET" else {"request": request, "data": request.POST}
    form = LoginForm(**attr)
    if request.method == "POST" and form.is_valid():
        user = form.user_cache
        login(request, user)
        flash_messages.success(request, "Sign in successful")
        return redirect("dashboard:home")
    return render(request, "accounts/login.html", {"form": form})


@login_required
def _logout(request):
    logout(request)
    return redirect("sign_in")


def password_reset_request(request):
    attr = {} if request.method == "GET" else {"data": request.POST}
    form = CustomPasswordResetForm(**attr)

    if request.method == "POST" and form.is_valid():
        is_sent = form.save()
        if is_sent:
            flash_messages.info(
                request,
                "A message with password reset instructions has been sent to your inbox.",
            )
            return redirect(reverse("sign_in"))
        else:
            flash_messages.error(request, "An error occurred, please try again")
            return redirect(reverse("sign_in"))
    return render(
        request=request,
        context={"form": form},
        template_name="registration/password_reset_form.html",
    )
