"""Session-based access control decorators.

Wraps view functions to enforce that the request has a TU session
(set by LoginApp.views.Login) and, optionally, the admin role.
"""

from functools import wraps

from django.shortcuts import redirect


def session_login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("username"):
            return redirect("login")
        if request.session.get("role") == "admin":
            return redirect("admin_dashboard")
        return view(request, *args, **kwargs)

    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("username"):
            return redirect("login")
        if request.session.get("role") != "admin":
            return redirect("home")
        return view(request, *args, **kwargs)

    return wrapper
