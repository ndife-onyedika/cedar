from datetime import date
from email.utils import make_msgid
import json
from calendar import month_abbr
from multiprocessing import context

from django.conf import settings as dj_sett
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import IntegrityError, transaction
from django.db.models.query_utils import Q
from django.http import JsonResponse
from django.shortcuts import resolve_url
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from notifications.models import Notification
from notifications.signals import notify

from accounts.models import Member, User
from cedar.mixins import (
    display_duration,
    display_rate,
    format_date_model,
    get_amount,
    get_data_equivalent,
    get_savings_total,
    get_shares_total,
)
from loans.forms import LoanRepaymentForm
from loans.mixins import check_loan_eligibility
from loans.models import LoanRepayment, LoanRequest
from savings.models import (
    SavingsCredit,
    SavingsDebit,
    SavingsInterest,
    SavingsInterestTotal,
    YearEndBalance,
)
from settings.models import AccountChoice
from shares.models import Shares, SharesTotal
from django.db.models.aggregates import Sum
from django.db.models import DateField, ExpressionWrapper


# Create your views here.
@login_required
@require_http_methods(["POST"])
def change_avatar(request, member_id):
    from accounts.models import Member

    data = {}
    image = request.FILES["image"]

    try:
        member = Member.objects.get(id=member_id)
    except Member.DoesNotExist:
        status = "error"
        message = "Error, refresh browser and try again."
    else:
        try:
            with transaction.atomic():
                member.avatar = image
                member.save()
        except IntegrityError as e:
            print(f"MEMBER-AVATAR-UPDATE-ERROR: {e}")
            status = "error"
            message = "Error updating profile photo"
        else:
            status = "success"
            message = "Profile photo updated"
    data["status"] = status
    data["message"] = message
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def register_member(request):
    from accounts.forms import RegistrationForm

    data = {}
    form = RegistrationForm(request.POST, request.FILES)
    if form.is_valid():
        status = "success"
        data["message"] = "Account registered successfully"
        form.save()
    else:
        status = "error"
        data["data"] = {
            field: error[0]["message"]
            for field, error in form.errors.get_json_data(escape_html=True).items()
        }
    data["status"] = status
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def update_member(request, member_id: int):
    from accounts.forms import EditMemberForm

    data = {}
    member = Member.objects.get(id=member_id)
    form = EditMemberForm(instance=member, data=request.POST)

    if form.is_valid():
        member = form.save()
        status = "success"
        data["message"] = "{} Account updated successfully".format(member.name)
    else:
        status = "error"
        data["data"] = {
            field: error[0]["message"]
            for field, error in form.errors.get_json_data(escape_html=True).items()
        }
    data["status"] = status
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def perform_action(request):
    data = {}
    _data = json.loads(request.POST.get("data"))
    if _data["context"] != "delete":
        try:
            with transaction.atomic():
                members = Member.objects.filter(id__in=_data["id"])
                for member in members:
                    if _data["context"] == "status":
                        member.is_active = not member.is_active
                    elif _data["context"] == "account":
                        member.account_type = AccountChoice.objects.get(
                            name__icontains="Staff"
                            if member.account_type.name == "Normal"
                            else "Normal"
                        )
                    member.save()
        except IntegrityError as e:
            print(f"MEMBER-STATUS-UPDATE-ERROR: {e}")
            status = "error"
            message = "Error changing member(s) status"
        else:
            status = "success"
            message = "Member status updated"
    else:
        contexts = {
            "shares": Shares,
            "members": Member,
            "loans": LoanRequest,
            "loans.repay": LoanRepayment,
            "savings.deb": SavingsDebit,
            "savings.cred": SavingsCredit,
        }

        try:
            with transaction.atomic():
                contexts[_data["sub_context"]].objects.filter(
                    id__in=_data["id"]
                ).delete()
        except IntegrityError as e:
            status = "error"
            message = "Error deleting records"
            print(f"SERVICE-DELETION-ERROR-{_data['sub_context'].upper()}: {e}")

        else:
            status = "success"
            message = "Records deleted"
    data["status"] = status
    data["message"] = message
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def service_create(request, context: str):
    from loans.forms import LoanRequestForm
    from savings.forms import SavingsCreditForm, SavingsDebitForm
    from shares.forms import ShareAddForm

    data = {}
    contexts = {
        "share": ShareAddForm,
        "loan": LoanRequestForm,
        "loan.repay": LoanRepaymentForm,
        "savings.deb": SavingsDebitForm,
        "savings.cred": SavingsCreditForm,
    }

    form = contexts[context](request.POST, request.FILES)

    if form.is_valid():
        status = "success"
        member = form.cleaned_data["member"]
        amount = form.cleaned_data["amount"]

        if context in ("loan", "saving.deb"):
            if not member.is_active:
                status = "error"
                data["message"] = "Transaction cannot be completed - ACCOUNT INACTIVE"
            if context == "loan":
                is_eligible = check_loan_eligibility(member, amount)
                if not is_eligible:
                    status = "error"
                    data[
                        "message"
                    ] = f"Transaction cannot be completed - Member do not have {member.account_type.lsr}% of loan in savings."

        if status == "success":
            try:
                with transaction.atomic():
                    model = form.save()
                    data["message"] = "Transaction completed"
                    verbs = {
                        "loan": [
                            "Loan",
                            "New Loan Disbursed",
                            member.name,
                            "loan request of {} has been disbursed.".format(
                                get_amount(amount)
                            ),
                        ],
                        "loan.repay": [
                            "Loan",
                            "Repayment",
                            member.name,
                            "loan repayment of {} has been recorded. Outstanding Amount: {}".format(
                                get_amount(amount),
                                get_amount(model.loan.outstanding_amount)
                                if hasattr(model, "loan")
                                else "",
                            ),
                        ],
                        "share": [
                            "Shares",
                            "New Share Added",
                            member.name,
                            "share of {} has been recorded. Total Shares: {}".format(
                                get_amount(amount), get_amount(get_shares_total(member))
                            ),
                        ],
                        "savings.cred": [
                            "Savings",
                            "New Savings Deposit",
                            member.name,
                            "deposit of {} has been recorded. Total Savings: {}".format(
                                get_amount(amount),
                                get_amount(get_savings_total(member).amount),
                            ),
                        ],
                        "savings.deb": [
                            "Savings",
                            "New Savings Withdrawal",
                            member.name,
                            "withdrawal of {} has been recorded. Total Savings: {}".format(
                                get_amount(amount),
                                get_amount(get_savings_total(member).amount),
                            ),
                        ],
                    }

                    verb = verbs[context]
                    notify.send(
                        User.objects.get(is_superuser=True),
                        level="success",
                        timestamp=timezone.now(),
                        verb="{}: {} - {}".format(verb[0], verb[1], verb[2]),
                        description="{}'s {}".format(member.name, verb[3]),
                        recipient=User.objects.exclude(is_superuser=False),
                    )
            except IntegrityError as e:
                status = "error"
                print(f"SERVICE-FORM-ERROR-{context.upper()}: {e}")
                data["message"] = "Transaction cannot be completed, try again"
    else:
        status = "error"
        data["data"] = {
            field: error[0]["message"]
            for field, error in form.errors.get_json_data(escape_html=True).items()
        }
    data["status"] = status
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def update_settings(request):
    from settings.models import BusinessYear
    from settings.forms import BusinessYearForm

    data = {}
    try:
        with transaction.atomic():
            form = BusinessYearForm(request.POST, instance=BusinessYear.objects.last())
            if form.is_valid():
                form.save()
                status = "success"
                data["message"] = "Settings updated successfully"
            else:
                status = "error"
                data["data"] = {
                    field: error[0]["message"]
                    for field, error in form.errors.get_json_data(
                        escape_html=True
                    ).items()
                }
    except IntegrityError as e:
        status = "error"
        data["message"] = "Error updating settings"
        print(f"UPDATE-SETTINGS-AJAX-ERROR: {e}")

    data["status"] = status
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def get_loan(request, member_id: str):
    from loans.models import LoanRequest

    data = {}
    member = Member.objects.get(id=member_id)
    try:
        loan = LoanRequest.objects.get(member=member, status="disbursed")
    except LoanRequest.DoesNotExist:
        status = "error"
        data["message"] = "Member does not have a loan that is not terminated."
    else:
        status = "success"
        data["data"] = [
            "{} | {} | {}".format(
                get_amount(amount=loan.amount),
                display_duration(loan.duration),
                format_date_model(loan.created_at),
            ),
            get_amount(loan.outstanding_amount),
        ]

    data["status"] = status
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def get_chart(request):
    data = {"chart": []}
    year = timezone.now().year
    for month in range(1, 13):
        data["chart"].append(
            {
                "month": month_abbr[month],
                "loans": LoanRequest.objects.filter(
                    created_at__month=month, created_at__year=year
                ).count(),
                "deposits": SavingsCredit.objects.filter(
                    created_at__month=month,
                    created_at__year=year,
                    reason="credit-deposit",
                ).count(),
                "withdrawals": SavingsDebit.objects.filter(
                    created_at__month=month,
                    created_at__year=year,
                    reason="debit-withdrawal",
                ).count(),
            }
        )

    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def data_table(request):
    def paginator_exec(page, per_page, content_list):
        paginator = Paginator(content_list, per_page)

        try:
            content = paginator.page(page)
        except PageNotAnInteger:
            content = paginator.page(1)
        except EmptyPage:
            content = paginator.page(paginator.num_pages)

        return content

    content_list = []
    data = {"content": [], "attr": {}}

    page = request.GET.get("page")
    sort_by = request.GET.get("sort_by")
    member_id = request.GET.get("member")
    table = request.GET.get("table_name")
    per_page = request.GET.get("per_page")
    search_by = request.GET.get("search_by")
    search_data = request.GET.get("search_data")
    table_context = request.GET.get("table_context")

    if search_by:
        text = search_data
        if search_by == "date" or search_by == "text-date":
            search_data = request.GET.getlist("search_data[]")
            date_range = search_data
            if search_by == "text-date":
                text = search_data[0]
                date_range = [search_data[1], search_data[2]]

    if member_id:
        member = Member.objects.get(id=member_id)

    tintr = 0
    if table == "members":
        content_list = Member.objects.all().order_by("name")
        table_context = table_context if table_context != "all" else None
        if table_context:
            content_list = content_list.filter(
                account_type=AccountChoice.objects.get(name__icontains=table_context)
            )
        if search_by:
            content_list = content_list.filter(
                Q(name__icontains=text) | Q(email__icontains=text)
            )

        content = paginator_exec(page, per_page, content_list)
        for i in content:
            c = {
                "id": i.id,
                "name": i.name,
                "acc_no": i.account_number,
                "created_at": i.date_joined,
                "acc_type": i.account_type.name,
                "balance": get_amount(get_savings_total(i).amount),
                "status": "Active" if i.is_active else "Inactive",
            }
            data["content"].append(c)
    elif table == "savings":
        savings_credit = SavingsCredit.objects.all()
        savings_debit = SavingsDebit.objects.all()
        if member_id:
            savings_credit = savings_credit.filter(member=member)
            savings_debit = savings_debit.filter(member=member)

        contexts = {
            "debit": savings_debit.order_by("-created_at"),
            "credit": savings_credit.order_by("-created_at"),
            "all": savings_credit.union(savings_debit).order_by("-created_at"),
        }
        content_list = contexts[table_context]

        if search_by == "date":
            content_list = (
                (
                    savings_credit.filter(created_at__date__range=date_range)
                    .union(savings_debit.filter(created_at__date__range=date_range))
                    .order_by("-created_at")
                )
                if table_context == "all"
                else contexts[table_context].filter(created_at__date__range=date_range)
            )
        elif search_by == "text":
            query = (
                Q(member__name__icontains=text)
                | Q(member__email__icontains=text)
                | Q(reason__icontains=text)
            )
            if table_context != "all":
                content_list = content_list.filter(query)
            else:
                content_list = (
                    savings_credit.filter(query)
                    .union(savings_debit.filter(query))
                    .order_by("-created_at")
                )
        elif search_by == "text-date":
            query = (
                Q(member__name__icontains=text)
                | Q(member__email__icontains=text)
                | Q(reason__icontains=text)
            )
            if table_context != "all":
                content_list = content_list.filter(
                    query,
                    created_at__date__range=date_range,
                )
            else:
                content_list = (
                    savings_credit.filter(
                        query,
                        created_at__date__range=date_range,
                    )
                    .union(
                        savings_debit.filter(
                            query,
                            created_at__date__range=date_range,
                        )
                    )
                    .order_by("-created_at")
                )

        content = paginator_exec(page, per_page, content_list)

        for i in content:
            c = {
                "id": i.id,
                "created_at": i.created_at,
                "amount": "{}{}".format(
                    "+" if i.reason.startswith("credit") else "-",
                    get_amount(amount=i.amount),
                ),
                "reason": get_data_equivalent(i.reason, "src"),
                **({} if member_id else {"mid": i.member.id, "name": i.member.name}),
            }
            data["content"].append(c)
    elif table == "savings.interest":
        contexts = {
            "all": SavingsInterest.objects.all().order_by(
                "-created_at", "member__name", "-total_interest"
            ),
            "each": SavingsInterestTotal.objects.all().order_by(
                "member__name", "-created_at"
            ),
        }

        def total_context_exec(
            text=None,
            date_range=[timezone.datetime(2014, 4, 1).date(), timezone.now().date()],
        ):
            start_date = (
                date_range[0]
                if isinstance(date_range[0], date)
                else timezone.datetime.strptime(date_range[0], "%Y-%m-%d").date()
            )
            end_date = (
                date_range[1]
                if isinstance(date_range[1], date)
                else timezone.datetime.strptime(date_range[1], "%Y-%m-%d").date()
            )
            data = (
                Member.objects.filter(
                    savingsinterest__created_at__date__range=date_range,
                    **({} if not text else {"name__icontains": text}),
                )
                .order_by("name")
                .annotate(t_interest=Sum("savingsinterest__interest"))
            )
            _date_range = "{} - {}".format(
                start_date.strftime("%d %b, %Y"), end_date.strftime("%d %b, %Y")
            )
            interest = data.aggregate(Sum("t_interest"))["t_interest__sum"] or 0
            return data, _date_range, interest

        if table_context != "total":
            content_list = contexts[table_context]
        else:
            content_list, _date_range, tintr = total_context_exec()

        if member_id:
            content_list = content_list.filter(member=member)

        if search_by == "date":
            if table_context != "total":
                content_list = content_list.filter(created_at__date__range=date_range)
            else:
                content_list, _date_range, tintr = total_context_exec(
                    date_range=date_range
                )
        elif search_by == "text":
            if table_context != "total":
                content_list = content_list.filter(
                    Q(member__name__icontains=text) | Q(member__email__icontains=text)
                )
            else:
                content_list, _date_range, tintr = total_context_exec(text=text)
        elif search_by == "text-date":
            if table_context != "total":
                content_list = content_list.filter(
                    Q(member__name__icontains=text) | Q(member__email__icontains=text),
                    created_at__date__range=date_range,
                )
            else:
                content_list, _date_range, tintr = total_context_exec(
                    text=text, date_range=date_range
                )

        content = paginator_exec(page, per_page, content_list)

        for i in content:
            c = {
                **(
                    {
                        "name": i.name,
                        "date_range": _date_range,
                        "interest": get_amount(amount=i.t_interest),
                    }
                    if table_context == "total"
                    else {
                        "id": i.id,
                        **(
                            {}
                            if member_id
                            else {"mid": i.member.id, "name": i.member.name}
                        ),
                        "amount": get_amount(amount=i.amount),
                        "savings_amount": get_amount(amount=i.savings.amount),
                        "interest": get_amount(amount=i.interest),
                        "created_at": i.created_at,
                        **(
                            {"updated_at": i.updated_at}
                            if table_context != "all"
                            else {"total_interest": get_amount(amount=i.total_interest)}
                        ),
                    }
                )
            }
            data["content"].append(c)
    elif table == "loans.repay":
        loan_id = request.GET.get("loan")
        try:
            content_list = LoanRepayment.objects.filter(
                loan=LoanRequest.objects.get(id=loan_id)
            ).order_by("-created_at")
        except LoanRequest.DoesNotExist:
            content_list = []
        else:
            if search_by == "date":
                content_list = content_list.filter(created_at__date__range=date_range)

        content = paginator_exec(page, per_page, content_list)
        for i in content:
            c = {
                "id": i.id,
                "created_at": i.created_at,
                "amount": get_amount(amount=i.amount),
            }
            data["content"].append(c)
    elif table == "loans":
        content_list = LoanRequest.objects.filter(status=table_context).order_by(
            "-created_at"
        )
        if member_id:
            content_list = content_list.filter(member=member)

        if search_by == "date":
            content_list = content_list.filter(created_at__date__range=date_range)
        elif search_by == "text":
            content_list = content_list.filter(
                Q(member__name__icontains=text) | Q(member__email__icontains=text)
            )
        elif search_by == "text-date":
            content_list = content_list.filter(
                Q(member__name__icontains=text) | Q(member__email__icontains=text),
                created_at__date__range=date_range,
            )

        content = paginator_exec(page, per_page, content_list)

        for i in content:
            c = {
                "id": i.id,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
                "rate": display_rate(i.interest_rate),
                "amount": get_amount(amount=i.amount),
                "duration": display_duration(i.duration),
                "guarantors": [
                    {
                        "mid": i.guarantor_1.id if i.guarantor_1 else "",
                        "name": i.guarantor_1.name if i.guarantor_1 else "-",
                    },
                    {
                        "mid": i.guarantor_2.id if i.guarantor_2 else "",
                        "name": i.guarantor_2.name if i.guarantor_2 else "-",
                    },
                ],
                **(
                    {"outstanding_amount": get_amount(i.outstanding_amount)}
                    if i.status == "disbursed"
                    else {"terminated_at": i.terminated_at}
                ),
                **({} if member_id else {"mid": i.member.id, "name": i.member.name}),
            }
            data["content"].append(c)
    elif table == "shares":
        content_list = SharesTotal.objects.all().order_by("member__name")
        if member_id:
            content_list = Shares.objects.filter(member=member).order_by("-created_at")

        if search_by == "date":
            content_list = content_list.filter(created_at__date__range=date_range)
        elif search_by == "text":
            content_list = content_list.filter(
                Q(member__name__icontains=text) | Q(member__email__icontains=text)
            )
        elif search_by == "text-date":
            content_list = content_list.filter(
                Q(member__name__icontains=text) | Q(member__email__icontains=text),
                created_at__date__range=date_range,
            )

        content = paginator_exec(page, per_page, content_list)

        for i in content:
            c = {
                "id": i.id,
                "created_at": i.created_at,
                "amount": get_amount(amount=i.amount),
                **(
                    {}
                    if member_id
                    else {
                        "mid": i.member.id,
                        "name": i.member.name,
                        "updated_at": i.updated_at,
                    }
                ),
            }
            data["content"].append(c)
    elif table == "eoy":
        content_list = YearEndBalance.objects.all().order_by(
            "member__name", "-created_at"
        )
        if member_id:
            content_list = content_list.filter(member=member).order_by("-created_at")
        if search_by == "date":
            content_list = content_list.filter(created_at__date__range=date_range)
        elif search_by == "text":
            content_list = content_list.filter(
                Q(member__name__icontains=text) | Q(member__email__icontains=text)
            )
        elif search_by == "text-date":
            content_list = content_list.filter(
                Q(member__name__icontains=text) | Q(member__email__icontains=text),
                created_at__date__range=date_range,
            )

        content = paginator_exec(page, per_page, content_list)

        for i in content:
            c = {
                "id": i.id,
                "created_at": i.created_at,
                "amount": get_amount(amount=i.amount),
                **({} if member_id else {"mid": i.member.id, "name": i.member.name}),
            }
            data["content"].append(c)
    data["attr"]["extra"] = {"total_interest": get_amount(tintr)}
    data["attr"]["has_other_pages"] = content.has_other_pages()
    data["attr"]["number"] = content.number
    data["attr"]["page_range"] = []
    data["attr"]["has_previous"] = content.has_previous()
    data["attr"]["has_next"] = content.has_next()
    if data["attr"]["has_previous"]:
        data["attr"]["prev"] = content.previous_page_number()
    if data["attr"]["has_next"]:
        data["attr"]["next"] = content.next_page_number()

    if data["attr"]["has_other_pages"]:
        for i in content.paginator.page_range:
            data["attr"]["page_range"].append(i)
    else:
        data["attr"]["page_range"].append(1)
    data["attr"]["per_page"] = int(per_page)
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def notify_unread_count(request):
    data = {"count": 0}

    notifications = Notification.objects.filter(
        recipient=request.user, unread=True
    ).exclude(deleted=True)
    data["count"] = notifications.count()
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def notify_list(request):
    count = request.GET.get("count")
    data = {"list": []}

    notifications = Notification.objects.filter(
        recipient=request.user,
    ).exclude(deleted=True)
    count = int(
        count
        if count != "*" and int(count) <= notifications.count()
        else notifications.count()
        if count == "*"
        else 10
    )
    notifications = notifications[:count]
    for notification in notifications:
        data["list"].append(
            {
                "id": notification.id,
                "unread": notification.unread,
                "verb": notification.verb,
                "description": notification.description,
                "timestamp": notification.timestamp,
                "level": notification.level,
            }
        )
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def notify_mark_read(request):
    notify_id = request.GET.get("id")
    data = {"mark_read": False}
    try:
        notification = Notification.objects.get(id=notify_id)
    except Notification.DoesNotExist:
        pass
    else:
        notification.unread = False
        notification.save()

        data["mark_read"] = True
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def notify_delete(request):
    notify_id = request.GET.get("id")
    data = {"is_deleted": False}
    try:
        notification = Notification.objects.get(id=notify_id)
    except Notification.DoesNotExist:
        pass
    else:
        if dj_sett.DJANGO_NOTIFICATIONS_CONFIG["SOFT_DELETE"]:
            notification.deleted = True
            notification.save()
        else:
            notification.delete()

        data["is_deleted"] = True

    return JsonResponse(data)
