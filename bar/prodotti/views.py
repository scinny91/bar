
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import ProdottoForm
from .models import Prodotto


@login_required
def nuovo_prodotto(request):
    if request.method == 'POST':
        form = ProdottoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_prodotti')  # puoi cambiare questa view come vuoi
    else:
        form = ProdottoForm()
    return render(request, 'prodotti/prodotto_form.html', {'form': form})

@login_required
def lista_prodotti(request):
    prodotti = Prodotto.objects.all()
    return render(request, 'prodotti/lista_prodotti.html', {'prodotti': prodotti})

@login_required
def modifica_prodotto(request, pk):
    prodotto = get_object_or_404(Prodotto, pk=pk)
    if request.method == 'POST':
        form = ProdottoForm(request.POST, instance=prodotto)
        if form.is_valid():
            form.save()
            return redirect('lista_prodotti')
    else:
        form = ProdottoForm(instance=prodotto)
    return render(request, 'prodotti/prodotto_form.html', {'form': form})

@login_required
def elimina_prodotto(request, pk):
    prodotto = get_object_or_404(Prodotto, pk=pk)
    if request.method == 'POST':
        prodotto.delete()
        return redirect('lista_prodotti')
    # opzionale: mostrare una pagina di conferma (altrimenti vai diretto alla lista)
    return render(request, 'prodotti/prodotto_conferma_elimina.html', {'prodotto': prodotto})