from django.shortcuts import render, redirect
from Bookingapp.models import LoginForm


# Create your views here.
def Login(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            print("there are user table")
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            request.session["username"] = username
            request.session["role"] = "lecturer"

            return redirect("home")

    data = {
        "form": form,
    }
    return render(request, "LoginApp/login.html", data)


def Logout(request):

    request.session.flush()

    return redirect("login")
