from django.urls import path

app_name = "dashboard"
urlpatterns = [
    path("", Dashboard.as_view(), name="home"),
    path("settings/<slug:slug>/", Profile.as_view(), name="settings"),
]
