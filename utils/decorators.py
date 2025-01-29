from curses import wrapper
from functools import wraps
import re

from django.shortcuts import redirect
from django.urls import reverse


def redirect_authenticated(to_view_name="", to_args=[], to_kwargs={}):
    def decorator_func(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                return redirect(reverse(to_view_name, args=to_args, kwargs=to_kwargs))
            else:
                return view_func(request, *args, **kwargs)

        return wrapper

    return decorator_func
