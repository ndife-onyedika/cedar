import json

from django.contrib import messages as flash_messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.db.models.aggregates import Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.urls import reverse
from django.views.generic import TemplateView

from accounts.models import Member, NextOfKin
from cedar.decorators import redirect_authenticated
from cedar.mixins import (
    get_amount,
    get_data_equivalent,
    get_savings_total,
    get_shares_total,
)
from loans.forms import LoanRepaymentForm, LoanRequestForm
from savings.forms import SavingsCreditForm, SavingsDebitForm
from savings.models import SavingsCredit, SavingsDebit, SavingsTotal
from settings.models import AccountChoice
from shares.forms import ShareAddForm

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
                        "title": "Add Member",
                        "class": "btn-primary",
                        "url": resolve_url("dashboard:members.add"),
                    }
                ],
            },
        }
        template = f"dashboard/pages/index.html"
        return render(request, template, context)


class MemberView(MemberListView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "savings": {},
            "member": member,
            "form": EditMemberForm(instance=member),
            "asf": ShareAddForm(initial={"member": member}),
            "lf": LoanRequestForm(initial={"member": member}),
            "swf": SavingsDebitForm(initial={"member": member}),
            "sdf": SavingsCreditForm(initial={"member": member}),
            "lrf": LoanRepaymentForm(initial={"member": member}),
            "dashboard": {
                "back": True,
                "context": "members",
                "title": "Member Details",
            },
        }
        st = get_savings_total(member=member)
        total_savings = st.amount
        total_savings_interest = st.interest
        savings_credit = SavingsCredit.objects.filter(member=member)
        savings_debit = SavingsDebit.objects.filter(member=member)
        last_credit = savings_credit.order_by("created_at").last()
        last_debit = savings_debit.order_by("created_at").last()
        total_shares = get_shares_total(member=member)
        context["shares"] = get_amount(amount=total_shares)
        context["savings"]["balance"] = get_amount(amount=total_savings)
        context["savings"]["interest"] = get_amount(amount=total_savings_interest)

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
        template = f"dashboard/pages/views/member/index.html"
        return render(request, template, context)

    def post(self, request, member_id: int, *args, **kwargs):
        data = {}
        code = 400
        status = "error"
        member = get_object_or_404(Member, id=member_id)
        form = EditMemberForm(instance=member, data=request.POST, files=request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
                    member = form.save()
            except IntegrityError as e:
                print(f"MEMBER-UPDATE-ERROR: {e}")
                code = 500
                data["message"] = "Error recording transaction"
            else:
                code = 200
                status = "success"
                data["message"] = "{} profile updated successfully".format(member.name)
        else:
            code = 400
            data["data"] = {
                field: error[0]["message"]
                for field, error in form.errors.get_json_data(escape_html=True).items()
            }
        data["status"] = status
        return JsonResponse(data, status=code)


@login_required
def registration_view(request):
    form = RegistrationForm(
        **(
            {}
            if request.method == "GET"
            else {"data": request.POST, "files": request.FILES}
        )
    )
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                member = form.save()
        except IntegrityError as e:
            print(f"REGISTRATION-ERROR: {e}")
            flash_messages.error(request, "Error adding account")
        else:
            flash_messages.success(request, "Member added successfully")
            return redirect("dashboard:members")
    return render(
        request,
        template_name="dashboard/pages/views/member/add.html",
        context={
            "form": form,
            "dashboard": {"back": True, "title": "Add Member", "context": "members"},
        },
    )


@redirect_authenticated(to_view_name="dashboard:home")
def login_view(request):
    attr = {} if request.method == "GET" else {"request": request, "data": request.POST}
    form = LoginForm(**attr)
    if request.method == "POST" and form.is_valid():
        user = form.user_cache
        login(request, user)
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
