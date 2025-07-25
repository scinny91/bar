from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Magazzino, Prodotto  # o il tuo path corretto
from .forms import ProdottoForm, ComponenteMagazzinoFormSet

@login_required
def modifica_prodotto(request, prodotto_id=None):
    prodotti = Prodotto.objects.all()

    if not prodotto_id and prodotti.exists():
        return redirect('elenco_anagrafiche_prodotti', prodotto_id=prodotti.first().id)

    prodotto = get_object_or_404(Prodotto, id=prodotto_id)

    if request.method == 'POST':
        prodotto_form = ProdottoForm(request.POST, instance=prodotto)
        formset = ComponenteMagazzinoFormSet(request.POST, instance=prodotto)

        if prodotto_form.is_valid() and formset.is_valid():
            prodotto_form.save()
            formset.save()
        return redirect('modifica_prodotto', prodotto_id=prodotto.id)
    else:
        prodotto_form = ProdottoForm(instance=prodotto)
        formset = ComponenteMagazzinoFormSet(instance=prodotto)

    return render(request, 'prodotti/anagrafica_prodotti.html', {
        'prodotti': prodotti,
        'prodotto': prodotto,
        'prodotto_form': prodotto_form,
        'formset': formset,
    })

@login_required
def aggiorna_giacenze(request):
    magazzino = Magazzino.objects.all().order_by('nome')

    if request.method == 'POST':
        modifiche = 0
        for voce in magazzino:
            nuova_quantita = request.POST.get(f"qty_{voce.id}")
            soglia_minima = request.POST.get(f"soglia_minima_{voce.id}")

            if nuova_quantita is not None:
                try:
                    # usa il manager per aggiornare
                    obj, creato = Magazzino.objects.aggiorna_o_crea(voce.nome, nuova_quantita, soglia_minima)
                    if not creato and obj.quantita != voce.quantita:
                        modifiche += 1
                except ValueError as e:
                    messages.error(request, f"{voce.nome}: {e}")

            # gestisce eventuale nuova riga
            nuovo_nome = request.POST.get("new_nome", "").strip()
            nuova_qta = request.POST.get("new_quantita", "").strip()
            soglia_minima = request.POST.get("new_soglia_minima", "").strip()

            if nuovo_nome and nuova_qta:
                try:
                    obj, creato = Magazzino.objects.aggiorna_o_crea(nuovo_nome, nuova_qta, soglia_minima)
                    if creato:
                        modifiche += 1
                        messages.success(request, f"Aggiunto nuovo articolo: {obj.nome}")
                    elif obj.quantita != int(nuova_qta):
                        modifiche += 1
                        messages.success(request, f"Giacenza aggiornata per {obj.nome}")
                except ValueError as e:
                    messages.error(request, f"{nuovo_nome}: {e}")

        if modifiche:
            messages.success(request, f"Giacenze aggiornate per {modifiche} articoli.")
        else:
            messages.info(request, "Nessuna modifica effettuata.")

        return redirect('aggiorna_giacenze')

    return render(request, 'prodotti/magazzino_giacenze.html', {'magazzino': magazzino})


@login_required
def elenco_anagrafiche_prodotti(request):
    prodotti = Prodotto.objects.all().order_by('nome')
    return render(request, 'prodotti/anagrafica_elenco.html', {'prodotti': prodotti})