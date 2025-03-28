import io
import traceback
from calendar import month_abbr
from datetime import date

from django.conf import settings as dj_sett
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import IntegrityError, transaction
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from notifications.models import Notification

from accounts.models import Member
from loans.models import LoanRepayment, LoanRequest
from savings.models import (
    SavingsCredit,
    SavingsDebit,
    SavingsInterest,
    SavingsInterestTotal,
    YearEndBalance,
)
from settings.models import AccountChoice
from shares.models import Shares
from utils.helpers import (
    display_duration,
    display_rate,
    exportPDF,
    get_amount,
    get_savings_total,
)

# Create your views here.


def total_context_exec(
    id=None,
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
            **({} if not id else {"id__in": id}),
            **({} if not text else {"name__icontains": text}),
            savingsinterest__created_at__date__range=date_range,
        )
        .order_by("name")
        .annotate(t_interest=Sum("savingsinterest__interest"))
    )
    _date_range = "{} - {}".format(
        start_date.strftime("%d %b, %Y"), end_date.strftime("%d %b, %Y")
    )
    interest = data.aggregate(Sum("t_interest"))["t_interest__sum"] or 0
    return data, _date_range, interest


@login_required
@require_http_methods(["POST"])
def service_create(request, context: str):
    from loans.views import LoanListView, loan_repayment_view
    from savings.views import savings_credit_view, savings_debit_view
    from shares.views import ShareListView

    data = {}
    contexts = {
        "loans": LoanListView().post,
        "shares": ShareListView().post,
        "savings.debit": savings_debit_view,
        "savings.credit": savings_credit_view,
        "loans.repayment": loan_repayment_view,
    }

    try:
        code, data["status"], data["message"], data["data"] = contexts[context](
            request=request
        )
    except Exception as e:
        traceback.print_exc()
        print("ERROR", f"{e}")
        code = 400
        data["status"] = "error"
        data["message"] = "Invalid Context"
    return JsonResponse(data, status=code)


@login_required
@require_http_methods(["POST"])
def service_update(request, context: str, id: int):
    from loans.views import LoanRepaymentView, LoanView
    from savings.views import SavingsCreditView, SavingsDebitView
    from shares.views import ShareView

    data = {}
    contexts = {
        "loans": LoanView().post,
        "shares": ShareView().post,
        "savings.debit": SavingsDebitView().post,
        "savings.credit": SavingsCreditView().post,
        "loans.repayment": LoanRepaymentView().post,
    }

    try:
        code, data["status"], data["message"], data["data"] = contexts[context](
            request=request, id=id
        )
    except Exception as e:
        print(f"{e}")
        code = 400
        data["status"] = "error"
        data["message"] = "Invalid Context"
    return JsonResponse(data, status=code)


@login_required
@require_http_methods(["GET"])
def service_fetch(request, context: str, id: int):
    from loans.views import LoanRepaymentView, LoanView
    from savings.views import SavingsCreditView, SavingsDebitView
    from shares.views import ShareView

    data = {}
    contexts = {
        "loans": LoanView().get,
        "shares": ShareView().get,
        "savings.debit": SavingsDebitView().get,
        "savings.credit": SavingsCreditView().get,
        "loans.repayment": LoanRepaymentView().get,
    }

    try:
        code, data["status"], data["message"], data["data"] = contexts[context](
            request=request, id=id
        )
    except Exception as e:
        print(f"{e}")
        code = 400
        data["status"] = "error"
        data["message"] = "Invalid Context"
    return JsonResponse(data, status=code)


@login_required
@require_http_methods(["POST"])
def service_delete(request, context: str):
    data = {}
    code = 403
    status = "error"
    message = "You cannot perform this action"

    contexts = {
        "shares": Shares,
        "members": Member,
        "loans": LoanRequest,
        "savings.debit": SavingsDebit,
        "savings.credit": SavingsCredit,
        "loans.repayment": LoanRepayment,
    }

    id = request.POST.getlist("id")

    try:
        context = contexts[context]
    except KeyError:
        code = 404
        message = "Resource Not Found"
    else:
        try:
            with transaction.atomic():
                context.objects.filter(id__in=id).delete()
        except IntegrityError as e:
            code = 500
            message = "Error deleting records"
            print(f"SERVICE-DELETION-ERROR-{context.upper()}: {e}")
        else:
            code = 200
            status = "success"
            message = "Record(s) deleted"

    data["status"] = status
    data["message"] = message
    return JsonResponse(data, status=code)


@login_required
@require_http_methods(["GET"])
def service_export(request, context: str):
    data = []
    contexts = {
        "shares": Shares,
        "loans": LoanRequest,
        "eoy": YearEndBalance,
        "members.all": Member,
        "members.true": Member,
        "members.false": Member,
        "savings.credit": SavingsCredit,
        "savings.debit": SavingsInterest,
        "loans.repayment": LoanRepayment,
        "savings_interest.all": SavingsInterest,
        "savings_interest.each": SavingsInterestTotal,
    }

    id_ = request.GET.getlist("id")
    range_ = request.GET.get("range")
    member_id = request.GET.get("member_id")
    member = Member.objects.get(id=member_id) if member_id else None

    if range_:
        range_ = range_.split(",")
        range_dates = [
            timezone.datetime.strptime(range_[0], "%Y-%m-%d").date(),
            timezone.datetime.strptime(range_[1], "%Y-%m-%d").date(),
        ]
        if context not in ("savings.all", "savings_interest.total"):
            range_ = "{} - {}".format(
                range_dates[0].strftime("%d %b, %Y"),
                range_dates[1].strftime("%d %b, %Y"),
            )

    if context not in ("savings.all", "savings_interest.total"):
        model = contexts[context]
        exports = model.objects.filter(**({"id__in": id_} if id_[0] != "*" else {}))

    if context == "savings.all":
        attr = {}
        savings_debit = SavingsDebit.objects.all()
        savings_credit = SavingsCredit.objects.all()

        if id_[0] != "*":
            attr["id__in"] = id_
        if range_:
            attr["created_at__date__range"] = range_dates

        exports = (
            savings_credit.filter(**attr)
            .union(savings_debit.filter(**attr))
            .order_by("-created_at")
        )
    if context == "savings_interest.total":
        exports, range_, total_interest = total_context_exec(
            **({} if id_[0] == "*" else {"id": id_}),
            **({"date_range": range_} if range_ else {}),
        )

    title = "{context}{member}{range}".format(
        range=f" ({range_})" if range_ else "",
        member=f" - {member.name}" if member else "",
        context=(
            "End of Year Balance"
            if context == "eoy"
            else " ".join(
                [k.capitalize() for k in context.replace("_", ".").split(".")]
            )
        ),
    )

    if len(exports) > 0:
        for item in exports:
            if context in ("members.all" "members.true" "members.false"):
                data.append(
                    {
                        "name": item.name,
                        "account_number": item.account_number,
                        "account_type": item.account_type.name,
                        "status": "Active" if item.is_active else "Inactive",
                        "balance": "NGN "
                        + get_amount(get_savings_total(item).amount)[1:],
                        "date_joined": item.date_joined.strftime("%d %b %Y, %H:%M %p"),
                    }
                )
            if context == "shares":
                data.append(
                    {
                        **({} if member else {"name": item.member.name}),
                        "amount": "NGN " + get_amount(amount=item.amount)[1:],
                        "created_at": item.created_at.strftime("%d %b %Y, %H:%M %p"),
                    }
                )
            if context == "loans":
                data.append(
                    {
                        **({} if member else {"name": item.member.name}),
                        "amount": "NGN " + get_amount(amount=item.amount)[1:],
                        "rate": display_rate(item.interest_rate),
                        "duration": display_duration(item.duration),
                        "guarantors": [
                            guarantor.name if guarantor else "-"
                            for guarantor in item.guarantors.all()
                            if item.guarantors.all().count() > 0
                        ],
                        **(
                            {
                                "outstanding_amount": "NGN "
                                + get_amount(item.outstanding_amount)[1:]
                            }
                            if item.status == "disbursed"
                            else {
                                "terminated_at": item.terminated_at.strftime(
                                    "%b %d, %y, %H:%M %p"
                                )
                            }
                        ),
                        "created_at": item.created_at.strftime("%d %b %Y, %H:%M %p"),
                        "updated_at": item.updated_at.strftime("%d %b %Y, %H:%M %p"),
                    }
                )
            if context == "loans.repayment":
                data.append(
                    {
                        "name": item.member.name,
                        "amount": "NGN " + get_amount(amount=item.amount)[1:],
                        "created_at": item.created_at.strftime("%d %b %Y, %H:%M %p"),
                    }
                )
            if context == "eoy":
                data.append(
                    {
                        **({} if member else {"name": item.member.name}),
                        "name": item.member.name,
                        "amount": "NGN " + get_amount(amount=item.amount)[1:],
                        "created_at": item.created_at.strftime("%d %b %Y, %H:%M %p"),
                    }
                )
            if context in ("savings.all", "savings.debit", "savings.credit"):
                data.append(
                    {
                        **({} if member else {"name": item.member.name}),
                        "amount": "NGN " + get_amount(amount=item.amount)[1:],
                        "reason": item.reason_display,
                        "created_at": item.created_at.strftime("%d %b %Y, %H:%M %p"),
                    }
                )

            if context in (
                "savings_interest.all",
                "savings_interest.each",
                "savings_interest.total",
            ):
                sub_context = context.split(".")[1]
                data.append(
                    {
                        **(
                            {
                                **({} if member else {"name": item.name}),
                                "date_range": range_,
                                "interest": "NGN "
                                + get_amount(amount=item.t_interest)[1:],
                            }
                            if sub_context == "total"
                            else {
                                **({} if member else {"name": item.member.name}),
                                "amount": "NGN " + get_amount(amount=item.amount)[1:],
                                "savings_amount": "NGN "
                                + get_amount(amount=item.savings.amount)[1:],
                                "interest": "NGN "
                                + get_amount(amount=item.interest)[1:],
                                "created_at": item.created_at.strftime(
                                    "%b %d, %y, %H:%M %p"
                                ),
                                **(
                                    {
                                        "updated_at": item.updated_at.strftime(
                                            "%b %d, %y, %H:%M %p"
                                        )
                                    }
                                    if sub_context != "all"
                                    else {
                                        "total_interest": "NGN "
                                        + get_amount(amount=item.total_interest)[1:]
                                    }
                                ),
                            }
                        )
                    }
                )

        pdf = exportPDF(title, data)
        buffer = io.BytesIO(pdf)
        buffer.seek(0)
        response = FileResponse(buffer, as_attachment=True)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = (
            'attachment; filename="export_{}{}.pdf"'.format(
                "".join(context.split(".")),
                (
                    "_{}".format("_".join(member.name.lower().split(" ")))
                    if member
                    else ""
                ),
            )
        )
    return response


@login_required
@require_http_methods(["POST"])
def update_settings(request):
    from settings.forms import BusinessYearForm
    from settings.models import BusinessYear

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
def get_loan(request, member_id: int):
    data = {}
    code = 404
    status = "error"
    message = "Not Found"

    try:
        member = Member.objects.get(id=member_id)
    except Member.DoesNotExist:
        pass
    else:
        try:
            loan = LoanRequest.objects.get(member=member, status="disbursed")
        except LoanRequest.DoesNotExist:
            status = "error"
            message = "Member does not have any disbursed loan."
        else:
            code = 200
            status = "success"
            message = "Loan Fetched"
            data["data"] = {
                "loan": loan.id,
                "outstanding": get_amount(loan.outstanding_amount),
            }

    data["status"] = status
    data["message"] = message
    return JsonResponse(data, status=code)


@login_required
@require_http_methods(["GET"])
def get_chart(request):
    data = {"chart": []}
    year = timezone.now().year
    for month in range(1, 13):
        data["chart"].append(
            {
                "month": month_abbr[month],
                "shares": (
                    Shares.objects.filter(
                        created_at__month=month, created_at__year=year
                    ).aggregate(Sum("amount"))["amount__sum"]
                    or 0
                )
                / 100,
                "deposits": (
                    SavingsCredit.objects.filter(
                        created_at__month=month,
                        created_at__year=year,
                        reason="credit-deposit",
                    ).aggregate(Sum("amount"))["amount__sum"]
                    or 0
                )
                / 100,
                "withdrawals": (
                    SavingsDebit.objects.filter(
                        created_at__month=month,
                        created_at__year=year,
                        reason="debit-withdrawal",
                    ).aggregate(Sum("amount"))["amount__sum"]
                    or 0
                )
                / 100,
                "loans": (
                    LoanRequest.objects.filter(
                        created_at__month=month, created_at__year=year
                    ).aggregate(Sum("amount"))["amount__sum"]
                    or 0
                )
                / 100,
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
    table = request.GET.get("table_name")
    per_page = request.GET.get("per_page")
    member_id = request.GET.get("member_id")
    search_text = request.GET.get("search_text")
    search_date = request.GET.get("search_date")
    table_context = request.GET.get("table_context")

    member = Member.objects.get(id=member_id) if member_id else None

    if table == "members":
        content_list = Member.objects.all()

        account_type = request.GET.get("account_type")
        account_number = request.GET.get("account_number")

        table_context = request.GET.get("table_context", "all").lower()
        if table_context not in ("all", "true", "false"):
            table_context = "all"

        content_list = content_list.filter(
            **({"is_active": table_context == "true"} if table_context != "all" else {})
        )

        if search_text:
            content_list = content_list.filter(
                Q(name__icontains=search_text) | Q(email__icontains=search_text)
            )
        if search_date:
            content_list = content_list.filter(
                date_joined__date__range=search_date.split(",")
            )

        if account_number and account_number.lower() != "null":
            content_list = content_list.filter(account_number__icontains=account_number)

        if account_type and account_type.lower() != "null":
            acc_choice = AccountChoice.objects.filter(name__icontains=account_type)
            if len(acc_choice) > 0:
                content_list = content_list.filter(account_type=acc_choice[0])

        content = paginator_exec(page, per_page, content_list)
        for i in content:
            c = {
                "id": i.id,
                "name": i.name,
                "is_active": i.is_active,
                "created_at": i.date_joined,
                "account_number": i.account_number,
                "account_type": i.account_type.name,
                "balance": get_amount(get_savings_total(i).amount),
            }
            data["content"].append(c)
    elif table == "shares":
        content_list = Shares.objects.all()

        if member:
            content_list = content_list.filter(member=member)

        updated_at = request.GET.get("updated_at")

        if search_text:
            content_list = content_list.filter(
                Q(member__name__icontains=search_text)
                | Q(member__email__icontains=search_text)
            )
        if search_date:
            content_list = content_list.filter(
                created_at__date__range=search_date.split(",")
            )

        if updated_at:
            content_list = content_list.filter(
                updated_at__date__range=updated_at.split(",")
            )

        content = paginator_exec(page, per_page, content_list)

        for i in content:
            c = {
                "id": i.id,
                "created_at": i.created_at,
                "amount": get_amount(amount=i.amount),
                **(
                    {}
                    if member
                    else {
                        "mid": i.member.id,
                        "name": i.member.name,
                    }
                ),
            }
            data["content"].append(c)
    elif table == "savings":
        savings_credit = SavingsCredit.objects.all()
        savings_debit = SavingsDebit.objects.all()
        if member:
            savings_credit = savings_credit.filter(member=member)
            savings_debit = savings_debit.filter(member=member)

        contexts = {
            "debit": savings_debit,
            "credit": savings_credit,
            "all": savings_credit.union(savings_debit).order_by("-created_at"),
        }

        reason = request.GET.get("reason")
        table_context = request.GET.get("table_context", "all").lower()

        if table_context not in ("all", "debit", "credit"):
            table_context = "all"
        content_list = contexts[table_context]

        if search_text:
            query = Q(member__name__icontains=search_text) | Q(
                member__email__icontains=search_text
            )
            if table_context != "all":
                content_list = contexts[table_context].filter(query)
            if table_context == "all":
                content_list = (
                    savings_credit.filter(query)
                    .union(savings_debit.filter(query))
                    .order_by("-created_at")
                )

        if search_date:
            date_range = search_date.split(",")
            if table_context != "all":
                content_list = contexts[table_context].filter(
                    created_at__date__range=date_range
                )
            if table_context == "all":
                content_list = (
                    savings_credit.filter(created_at__date__range=date_range)
                    .union(savings_debit.filter(created_at__date__range=date_range))
                    .order_by("-created_at")
                )

        if reason and reason.lower() != "null":
            if table_context != "all":
                content_list = contexts[table_context].filter(reason__icontains=reason)
            if table_context == "all":
                content_list = (
                    savings_credit.filter(reason__icontains=reason)
                    .union(savings_debit.filter(reason__icontains=reason))
                    .order_by("-created_at")
                )

        content = paginator_exec(page, per_page, content_list)

        for i in content:
            c = {
                "id": i.id,
                "created_at": i.created_at,
                "reason": i.reason_display,
                "amount": "{}{}".format(
                    "+" if i.reason.startswith("credit") else "-",
                    get_amount(amount=i.amount),
                ),
                **({} if member else {"mid": i.member.id, "name": i.member.name}),
            }
            data["content"].append(c)
    elif table == "savings_interest":
        total_interest = 0
        contexts = {
            "all": SavingsInterest.objects.all(),
            "each": SavingsInterestTotal.objects.all(),
        }

        if table_context != "total":
            content_list = contexts[table_context]
        else:
            content_list, _date_range, total_interest = total_context_exec()

        if member:
            content_list = content_list.filter(
                **(
                    {"id": member.id}
                    if table_context == "total"
                    else {"savings__member": member}
                )
            )

        if search_text:
            if table_context != "total":
                content_list = content_list.filter(
                    Q(savings__member__name__icontains=search_text)
                    | Q(savings__member__email__icontains=search_text)
                )
            else:
                content_list, _date_range, tintr = total_context_exec(text=search_text)

        if search_date:
            date_range = search_date.split(",")
            if table_context != "total":
                content_list = content_list.filter(created_at__date__range=date_range)
            else:
                content_list, _date_range, total_interest = total_context_exec(
                    date_range=date_range
                )

        if table_context == "total":
            data["attr"]["extra"] = {"total_interest": get_amount(total_interest)}

        content = paginator_exec(page, per_page, content_list)
        for i in content:
            c = {
                **(
                    {
                        "id": i.id,
                        "name": i.name,
                        "date_range": _date_range,
                        "interest": get_amount(amount=i.t_interest),
                    }
                    if table_context == "total"
                    else {
                        "id": i.id,
                        "created_at": i.created_at,
                        "amount": get_amount(amount=i.amount),
                        "interest": get_amount(amount=i.interest),
                        "savings_amount": get_amount(amount=i.savings.amount),
                        **(
                            {"updated_at": i.updated_at}
                            if table_context != "all"
                            else {"total_interest": get_amount(amount=i.total_interest)}
                        ),
                        **(
                            {}
                            if member
                            else {"mid": i.member.id, "name": i.member.name}
                        ),
                    }
                )
            }
            data["content"].append(c)
    elif table == "eoy":
        content_list = YearEndBalance.objects.all()
        if member:
            content_list = content_list.filter(member=member).order_by("-created_at")

        if search_date:
            content_list = content_list.filter(
                created_at__date__range=search_date.split(",")
            )
        if search_text:
            content_list = content_list.filter(
                Q(member__name__icontains=search_text)
                | Q(member__email__icontains=search_text)
            )

        content = paginator_exec(page, per_page, content_list)

        for i in content:
            c = {
                "id": i.id,
                "created_at": i.created_at,
                "amount": get_amount(amount=i.amount),
                **({} if member else {"mid": i.member.id, "name": i.member.name}),
            }
            data["content"].append(c)
    elif table == "loans":
        content_list = LoanRequest.objects.filter(status=table_context)
        if member:
            content_list = content_list.filter(member=member)

        if search_date:
            content_list = content_list.filter(
                created_at__date__range=search_date.split(",")
            )
        if search_text:
            content_list = content_list.filter(
                Q(member__name__icontains=search_text)
                | Q(member__email__icontains=search_text)
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
                        "mid": guarantor.id if guarantor else "",
                        "name": guarantor.name if guarantor else "-",
                    }
                    for guarantor in i.guarantors.all()
                    if i.guarantors.all().count() > 0
                ],
                **(
                    {"outstanding_amount": get_amount(i.outstanding_amount)}
                    if i.status == "disbursed"
                    else {"terminated_at": i.terminated_at}
                ),
                **({} if member else {"mid": i.member.id, "name": i.member.name}),
            }
            data["content"].append(c)
    elif table == "loans.repayment":
        loan_id = request.GET.get("loan_id")
        loan = LoanRequest.objects.filter(id=loan_id)
        if not len(loan) > 0:
            content_list = []
        else:
            loan = loan[0]
            content_list = LoanRepayment.objects.filter(loan=loan)
            if search_date:
                content_list = content_list.filter(
                    created_at__date__range=search_date.split(",")
                )

        content = paginator_exec(page, per_page, content_list)
        for i in content:
            c = {
                "id": i.id,
                "name": i.member.name,
                "created_at": i.created_at,
                "amount": get_amount(amount=i.amount),
            }
            data["content"].append(c)

    data["attr"]["current"] = content.number
    data["attr"]["pages"] = content.paginator.num_pages
    data["attr"]["prev"] = (
        content.previous_page_number() if content.has_previous() else None
    )
    data["attr"]["next"] = content.next_page_number() if content.has_next() else None

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
    data["count"] = notifications.count()
    count = int(count) if int(count) <= notifications.count() else notifications.count()
    notifications = notifications[:count]
    for notification in notifications:
        data["list"].append(
            {
                "id": notification.id,
                "verb": notification.verb,
                "level": notification.level,
                "unread": notification.unread,
                "timestamp": notification.timestamp,
                "description": notification.description,
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
