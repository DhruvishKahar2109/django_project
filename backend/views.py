from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required


def admin_login(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:

            messages.warning(
                request,
                "Please enter email and password."
            )

            return render(request, "admin_login.html")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            messages.success(
                request,
                "Login successful! Welcome back."
            )

            return redirect("dashboard")

        else:

            messages.error(
                request,
                "Invalid email or password."
            )

            return render(request, "admin_login.html")

    return render(request, "admin_login.html")

@login_required
def dashboard(request):
    return render(request, "dashboard.html")

@login_required
def categories(request):
    return render(request, "categories.html")


def admin_logout(request):
    logout(request)
    return redirect("login")