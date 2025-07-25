from django.urls import reverse
from collections import defaultdict
from django.utils.timezone import localdate
from django.db.models.functions import TruncDate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from bar.ordini.models import Ordine, OrdineRiga, STATUS_CHOICES, OPTION_CHOICES
from bar.prodotti.models import Prodotto, CATEGORIE_PRODOTTO, SOTTOCATEGORIE_PRODOTTO

from bar.core import Stato, Opzione, Categoria, Sottocategoria

from datetime import datetime


@login_required
def nuovo_ordine(request):
    prodotti = Prodotto.objects.all().order_by('categoria', 'sottocategoria', 'nome')
    if request.method == 'POST':
        ordine = Ordine()
        ordine.modifica_da_post_request(request.POST, prodotti)
        messages.success(request, f"Ordine #{ordine.id}-{ordine.cliente} inserito con successo.")
        return redirect('lista_ordini')


    prodotti_con_righe = []
    for prodotto in prodotti:
        righe = [{'quantita': 0, 'opzioni': ''}]  # riga vuota
        prodotti_con_righe.append({
            'nome': prodotto.nome,
            'righe': righe,
            'categoria': prodotto.categoria,
            'sottocategoria': prodotto.sottocategoria,
            'prezzo': prodotto.prezzo,
            'id': prodotto.id
        })
    context = {
        'titolo_pagina': 'Nuovo Ordine',
        'bottone_submit': 'Inserisci Ordine',
        'quantità': {},  # vuoto all'inizio
        'nome_ordine': '', # vuoto all'inizio
        'prodotti': prodotti_con_righe,
        'opzioni': OPTION_CHOICES,
        'is_new': True
    }
    return render(request, 'ordini/ordine_form.html', context)

@login_required
def lista_ordini(request):
    data_ordine = request.GET.get('data_ordine')
    data_ordine, data_precedente, data_successiva = ottieni_data_ordine_precedente_successiva(data_ordine)
    StatoAttesa = Stato.objects.get(chiave='in_attesa')
    StatoInPreparazione = Stato.objects.get(chiave='in_preparazione')
    ordini = Ordine.objects.filter(creato__date=data_ordine, stato__in=[StatoAttesa, StatoInPreparazione]).order_by('creato')
    totali = Ordine.calcola_totali(ordini)
    context = { "ordini": ordini,
                "totali_per_stato_cat_sottocat": totali,
                "date": data_ordine.strftime('%d-%m-%Y'),
                "data_precedente": data_precedente,
                "data_successiva": data_successiva,
                "is_riepilogo": False
    }

    return render(request, "ordini/lista_ordini.html", context)

@login_required
def riepilogo_ordini(request):
    data_ordine = request.GET.get('data_ordine')
    data_ordine, data_precedente, data_successiva = ottieni_data_ordine_precedente_successiva(data_ordine)
    ordini = Ordine.objects.filter(creato__date=data_ordine).order_by('creato')
    totali = Ordine.calcola_totali(ordini)
    context = { "ordini": ordini,
                "totali_per_stato_cat_sottocat": totali,
                "date": data_ordine.strftime('%d-%m-%Y'),
                "data_precedente": data_precedente,
                "data_successiva": data_successiva,
                "is_riepilogo": True
    }

    return render(request, "ordini/lista_ordini.html", context)


@login_required
def modifica_ordine(request, pk):

    ordine = get_object_or_404(Ordine, id=pk)
    prodotti = Prodotto.objects.all().order_by('categoria', 'sottocategoria', 'nome')

    if request.method == 'POST':
        ordine.modifica_da_post_request(request.POST, prodotti)
        messages.success(request, f"Ordine #{ordine.id}-{ordine.cliente} modificato con successo.")

        return redirect('lista_ordini')

    # Raggruppa righe per prodotto
    righe_per_prodotto = defaultdict(list)
    for riga in ordine.items.all():
        righe_per_prodotto[riga.prodotto_id].append({
            'quantita': riga.quantita,
            'opzioni': riga.opzioni,
        })

    prodotti_con_righe = []
    for prodotto in prodotti:
        righe = righe_per_prodotto.get(prodotto.id)
        if not righe:
            righe = [{'quantita': 0, 'opzioni': ''}]  # riga vuota
        prodotti_con_righe.append({
            'nome': prodotto.nome,
            'righe': righe,
            'categoria': prodotto.categoria,
            'sottocategoria': prodotto.sottocategoria,
            'prezzo': prodotto.prezzo,
            'id': prodotto.id
        })
    context = {
        'titolo_pagina': f'Modifica Ordine #{ordine.id}',
        'bottone_submit': 'Salva Modifiche',
        'nome_ordine': ordine.cliente,
        'prodotti': prodotti_con_righe,
        'opzioni': OPTION_CHOICES,
        'is_new': False,
    }
    return render(request, 'ordini/ordine_form.html', context)


@login_required
def elimina_ordine(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    ordine.delete()
    return redirect('lista_ordini')

@login_required
def conferma_ordine(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    stato = get_object_or_404(Stato, chiave="in_preparazione")
    ordine.cambia_stato_righe(stato)
    messages.success(request, f"Ordine #{ordine.id}-{ordine.cliente} confermato con successo.")
    return redirect('lista_ordini')


@login_required
def evasione(request):
    data_ordine = request.GET.get('data_ordine')
    data_ordine, data_precedente, data_successiva = ottieni_data_ordine_precedente_successiva(data_ordine)
    righe = OrdineRiga.objects.righe_da_evadere(data_ordine, stati_ordine=["in_preparazione"])
    righe_raggruppate = OrdineRiga.objects.righe_raggruppate_per_categoria(righe)

    return render(request, 'ordini/evasione.html', {
        'righe_raggruppate': righe_raggruppate,
        'is_consegna': False,
        'title': f"Ordini da evadere {data_ordine.strftime('%d-%m-%Y')}"
    })

@login_required
def consegne(request):
    if request.method == 'POST':
        riga_id = request.POST.get('riga_id')
        nuovo_stato = request.POST.get('nuovo_stato')

        riga = get_object_or_404(OrdineRiga, id=riga_id)
        riga.stato = nuovo_stato
        riga.save()

        return redirect(request.path)  # ricarica la pagina

    data_ordine = request.GET.get('data_ordine')
    data_ordine, data_precedente, data_successiva = ottieni_data_ordine_precedente_successiva(data_ordine)
    righe = OrdineRiga.objects.righe_da_evadere(data_ordine, stati_ordine=["in_preparazione", "non_trovato"])
    righe_raggruppate = OrdineRiga.objects.righe_raggruppate_per_categoria(righe)

    return render(request, 'ordini/evasione.html', {
        'righe_raggruppate': righe_raggruppate,
        'is_consegna': True,
        'title': f"Ordini da consegnare {data_ordine.strftime('%d-%m-%Y')}",

    })

@login_required
def set_stato_riga_ordine(request, pk="", stato=""):
    riga = get_object_or_404(OrdineRiga, id=pk)
    nuovo_stato = get_object_or_404(Stato, chiave=stato)
    riga.stato = nuovo_stato
    riga.save()
    # Recupera il parametro data_ordine, se presente
    data_ordine = request.GET.get('data_ordine')

    messages.success(request, f"Ordine #{riga.ordine.id}.{riga.id} passata in {riga.stato.valore}")

    # Costruisci l’URL con il parametro
    url = reverse('consegne')
    if data_ordine:
        url += f"?data_ordine={data_ordine}"
    return redirect(url)



def ottieni_data_ordine_precedente_successiva(data_ordine):
    if not data_ordine:
        data_ordine = localdate()    # restituisce la data odierna (timezone aware)
    else:
        data_ordine = datetime.strptime(data_ordine, '%d-%m-%Y')


    date_distinte = Ordine.objects.annotate(data=TruncDate('creato')) \
        .values_list('data', flat=True) \
        .distinct()

    # Data precedente a oggi
    data_precedente = date_distinte.filter(data__lt=data_ordine).order_by('-data').first()
    if data_precedente:
        data_precedente = data_precedente.strftime('%d-%m-%Y')
    else:
        data_precedente = ""

    # Data successiva a oggi
    data_successiva = date_distinte.filter(data__gt=data_ordine).order_by('data').first()
    if data_successiva:
        data_successiva = data_successiva.strftime('%d-%m-%Y')
    else:
        data_successiva = ""
    return data_ordine, data_precedente, data_successiva