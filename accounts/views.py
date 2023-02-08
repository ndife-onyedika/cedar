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
from settings.models import AccountChoice

from .forms import CustomPasswordResetForm, LoginForm, RegistrationForm


# Create your views here.
class MemberListView(LoginRequiredMixin, TemplateView):
    def get(self, request, context: str, *args, **kwargs):
        if context not in ("all", "normal", "staff"):
            raise Http404
        context = {
            "dashboard": {
                "title": "Members",
                "context": "members",
                "sub_context": context,
                "buttons": [
                    {
                        "title": "Add Member",
                        "class": "btn-primary",
                        "url": resolve_url("dashboard:members.add"),
                    }
                ],
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class MemberView(MemberListView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "members",
                "title": "Member Details",
                "buttons": [
                    {
                        "title": "Set {}".format(
                            "Active" if not member.is_active else "Inactive"
                        ),
                        "class": "btn-{}".format(
                            "danger" if not member.is_active else "primary"
                        ),
                    },
                    {"title": "Edit", "class": "btn-primary"},
                    {"title": "Delete", "class": "btn-danger"},
                ],
            },
        }
        template = f"accounts/pages/member.html"
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
