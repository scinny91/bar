
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout


def user_login(request):
    if request.method == "POST":
        user = authenticate(
            request, username=request.POST["username"], password=request.POST["password"]
        )
        if user:
            login(request, user)
            return redirect("lista_ordini")
    return render(request, "bar/login.html")

def user_logout(request):
    logout(request)
    return redirect("login")
