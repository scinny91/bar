from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Magazzino  # o il tuo path corretto
from django.db.models import F

def aggiorna_giacenze(request):
    magazzino = Magazzino.objects.all().order_by('nome')

    if request.method == 'POST':
        modifiche = 0
        for voce in magazzino:
            field_name = f"qty_{voce.id}"
            nuova_quantita = request.POST.get(field_name)
            if nuova_quantita is not None:
                try:
                    nuova_quantita = int(nuova_quantita)
                    if nuova_quantita != voce.quantita:
                        voce.quantita = nuova_quantita
                        voce.save()
                        modifiche += 1
                except ValueError:
                    messages.error(request, f"Valore non valido per {voce.nome}")

        if modifiche:
            messages.success(request, f"Giacenze aggiornate per {modifiche} articoli.")
        else:
            messages.info(request, "Nessuna modifica effettuata.")

        return redirect('aggiorna_giacenze')

    return render(request, 'prodotti/magazzino_giacenze.html', {'magazzino': magazzino})