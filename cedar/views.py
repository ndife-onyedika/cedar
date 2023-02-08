from django.shortcuts import redirect


def index(request):
    return redirect(
        "sign_in" if not request.user.is_authenticated else "dashboard:home",
    )
