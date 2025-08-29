
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout


def user_login(request):
    if request.method == "POST":
        user = authenticate(
            request, username=request.POST["username"], password=request.POST["password"]
        )
        if user:
            login(request, user)
            next_url = request.GET.get("next")  # controlla se c'è il parametro
            if next_url:
                return redirect(next_url)
            return redirect("dashboard")
    return render(request, "bar/login.html")

def user_logout(request):
    logout(request)
    return redirect("login")
