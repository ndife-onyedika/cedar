from django.urls import path

from accounts.views import MemberListView, MemberView, registration_view
from dashboard.views import Dashboard, Settings
from loans.views import LoanListView, LoanOverview
from savings.views import (
    SavingsInterestListView,
    SavingsListView,
    YearEndBalanceListView,
)
from shares.views import ShareListView

app_name = "dashboard"
urlpatterns = [
    path("", Dashboard.as_view(), name="home"),
    path("settings/", Settings.as_view(), name="settings"),
    path("members/", MemberListView.as_view(), name="members"),
    path("members/add/", registration_view, name="members.add"),
    path("members/<int:member_id>/", MemberView.as_view(), name="members.details"),
    path("savings/", SavingsListView.as_view(), name="savings"),
    path(
        "savings/interests/", SavingsInterestListView.as_view(), name="savings_interest"
    ),
    path("loans/", LoanListView.as_view(), name="loans"),
    path("loans/<int:loan_id>/", LoanOverview.as_view(), name="loans.details"),
    path("shares/", ShareListView.as_view(), name="shares"),
    path("year-end-balance/", YearEndBalanceListView.as_view(), name="eoy"),
]
