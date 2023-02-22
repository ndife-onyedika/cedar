from django.urls import path
from accounts.views import MemberListView, MemberView

from dashboard.views import Dashboard, Settings
from loans.views import LoanListView, LoanView, MemberLoanListView
from savings.views import (
    MemberSavingsInterestsListView,
    MemberSavingsListView,
    MemberYearEndBalancesListView,
    SavingsInterestListView,
    SavingsListView,
    YearEndBalanceListView,
)
from shares.views import MemberSharesListView, ShareListView

app_name = "dashboard"
urlpatterns = [
    path("", Dashboard.as_view(), name="home"),
    path("settings/", Settings.as_view(), name="settings"),
    path("members/", MemberListView.as_view(), name="members"),
    path("members/<int:member_id>/", MemberView.as_view(), name="members.details"),
    path("savings/", SavingsListView.as_view(), name="savings"),
    path(
        "savings/<int:member_id>/",
        MemberSavingsListView.as_view(),
        name="savings.member",
    ),
    path(
        "savings/interests/", SavingsInterestListView.as_view(), name="savings.interest"
    ),
    path(
        "savings/<int:member_id>/interests/",
        MemberSavingsInterestsListView.as_view(),
        name="savings.interest.member",
    ),
    path("loans/", LoanListView.as_view(), name="loans"),
    path("loans/<int:member_id>/", MemberLoanListView.as_view(), name="loans.member"),
    path("shares/", ShareListView.as_view(), name="shares"),
    path(
        "shares/<int:member_id>/", MemberSharesListView.as_view(), name="shares.member"
    ),
    path("year-end-balance/", YearEndBalanceListView.as_view(), name="eoy"),
    path(
        "year-end-balance/<int:member_id>/",
        MemberYearEndBalancesListView.as_view(),
        name="eoy.member",
    ),
]
