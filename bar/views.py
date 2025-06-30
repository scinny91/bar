
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone

from bar.ordini.models import Ordine, OrdineRiga
from bar.prodotti.models import Prodotto

def user_login(request):
    if request.method == "POST":
        user = authenticate(
            request, username=request.POST["username"], password=request.POST["password"]
        )
        if user:
            login(request, user)
            return redirect("cassa")
    return render(request, "bar/login.html")

def user_logout(request):
    logout(request)
    return redirect("login")

@login_required
def cassa(request):
    prodotti = Prodotto.objects.all()
    if request.method == "POST":
        ordine = Ordine.objects.create(stato="in_attesa", created_at=timezone.now())
        for prodotto in prodotti:
            qty = int(request.POST.get(f"qty_{prodotto.id}", 0))
            if qty > 0:
                OrdineRiga.objects.create(ordine=ordine, prodotto=prodotto, quantita=qty)
        return redirect("cassa")
    return render(request, "bar/cassa.html", { "prodotti": prodotti })

@login_required
def cucina(request):
    ordini = Ordine.objects.prefetch_related("items__prodotto").order_by("-creato")
    if request.method == "POST":
        ordine = Ordine.objects.get(pk=request.POST["ordine_id"])
        ordine.status = request.POST["nuovo_stato"]
        ordine.save()
        return redirect("cucina")
    return render(request, "bar/cucina.html", { "ordini": ordini })

