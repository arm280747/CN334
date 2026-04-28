from django.shortcuts import render, redirect
from Bookingapp.models import LoginForm, User

from .tu_api import TUAPIError, verify_credentials


def Login(request):
    if request.session.get("username"):
        if request.session.get("role") == "admin":
            return redirect("admin_dashboard")
        return redirect("home")

    form = LoginForm()
    error = None

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            try:
                tu_user = verify_credentials(username, password)
            except TUAPIError as exc:
                tu_user = None
                error = f"ไม่สามารถติดต่อระบบ TU REST API ได้: {exc}"

            if tu_user is not None:
                user = _sync_user(tu_user)

                request.session["username"] = user.username
                request.session["role"] = user.role
                request.session["display_name"] = (
                    tu_user["display_name_th"] or tu_user["display_name_en"]
                )
                request.session["email"] = tu_user["email"]

                if user.role == "admin":
                    return redirect("admin_dashboard")
                return redirect("home")

            if error is None:
                error = "Username หรือ Password ไม่ถูกต้อง"

    data = {
        "form": form,
        "error": error,
    }
    return render(request, "LoginApp/login.html", data)


def Logout(request):
    request.session.flush()
    return redirect("login")


def _sync_user(tu_user):
    """Upsert a local User row from TU API data, preserving any existing role."""

    display_name = tu_user["display_name_th"] or tu_user["display_name_en"]
    defaults = {
        "name": display_name,
        "email": tu_user["email"],
        "user_id": tu_user["username"],
    }

    user, created = User.objects.get_or_create(
        username=tu_user["username"],
        defaults={**defaults, "role": "lecturer"},
    )

    changed = created
    for field, value in defaults.items():
        if value and getattr(user, field) != value:
            setattr(user, field, value)
            changed = True

    if not user.role:
        user.role = "lecturer"
        changed = True

    if changed:
        user.save()

    return user
