from silk.profiling.profiler import silk_profile

from django.urls import reverse
from django.db import models
from django.core.cache import cache
from django.utils.timezone import localdate
from django.db.models.functions import TruncDate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from collections import defaultdict
from datetime import datetime

from bar.ordini.models import Ordine, OrdineRiga, STATUS_CHOICES, OPTION_CHOICES
from bar.prodotti.models import Prodotto, CATEGORIE_PRODOTTO, SOTTOCATEGORIE_PRODOTTO, ComponenteMagazzino, prodottoError
from bar.core import Stato, Opzione, Categoria, Sottocategoria


@login_required
@silk_profile()
def nuovo_ordine(request):
    prodotti = Prodotto.objects.filter(stato='valido').order_by('sottocategoria__categoria', 'sottocategoria', 'nome')
    if request.method == 'POST':
        ordine = Ordine()
        ordine.utente = request.user
        ordine.modifica_da_post_request(request.POST, prodotti)
        messages.success(request, f"Ordine #{ordine.id}-{ordine.cliente} inserito con successo.")
        return redirect('lista_ordini')


    prodotti_con_righe = []
    for prodotto in prodotti:
        righe = [{'quantita': 0, 'opzioni': ''}]  # riga vuota
        prodotti_con_righe.append({
            'nome': prodotto.nome,
            'righe': righe,
            'categoria': prodotto.sottocategoria.categoria,
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
@silk_profile()
def lista_ordini(request):
    data_ordine = request.GET.get('data_ordine')

    # Ottieni gli stati dalla cache o dal DB
    stati_cache = cache.get("stati")
    if not stati_cache:
        stati_cache = {s.chiave: s for s in Stato.objects.all()}
        cache.set("stati", stati_cache, timeout=3600)  # 1 ora

    StatoAttesa = stati_cache.get('in_attesa')
    StatoInPreparazione = stati_cache.get('in_preparazione')
    StatoParzialmenteCompletato = stati_cache.get('parzialmente_completato')

    # Calcolo date precedente e successiva
    data_ordine, data_precedente, data_successiva = ottieni_data_ordine_precedente_successiva(
        data_ordine,
        stati_ammessi=[StatoAttesa, StatoInPreparazione, StatoParzialmenteCompletato]
    )

    # Query ottimizzata: select_related + prefetch_related
    ordini = Ordine.objects.filter(
        creato__date=data_ordine,
        stato__in=[StatoAttesa, StatoInPreparazione, StatoParzialmenteCompletato]
    ).order_by('creato').select_related(
        'stato'
    ).prefetch_related(
        'items__prodotto',
        'items__stato',
        'items__opzioni'
    )

    # Totali calcolati come prima
    totali = Ordine.calcola_totali(ordini)

    context = {
        "ordini": ordini,
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
    StatoCompletato = Stato.objects.get(chiave='Completato')
    StatoParzialmenteCompletato = Stato.objects.get(chiave='parzialmente_completato')
    data_ordine, data_precedente, data_successiva = ottieni_data_ordine_precedente_successiva(data_ordine,
                                                                                              stati_ammessi=[
                                                                                                  StatoParzialmenteCompletato,
                                                                                                  StatoCompletato])
    ordini = Ordine.objects.filter(creato__date=data_ordine, stato__in=[StatoCompletato, StatoParzialmenteCompletato]).order_by(
        'creato')


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
    prodotti = Prodotto.objects.all().order_by('sottocategoria__categoria', 'sottocategoria', 'nome')

    if request.method == 'POST':
        ordine.utente = request.user
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
            'categoria': prodotto.sottocategoria.categoria,
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
    # Ripristina giacenza se era stata scalata (in_preparazione o completato)
    for item in ordine.items.select_related('prodotto', 'stato'):

        if item.stato.chiave in ("completato", "in_preparazione"):
            componenti = ComponenteMagazzino.objects.filter(prodotto=item.prodotto).select_related('magazzino')
            for componente in componenti:
                da_ripristinare = componente.quantita_totale_per(item.quantita)
                componente.magazzino.quantita = models.F('quantita') + da_ripristinare
                componente.magazzino.save()
    ordine.delete()
    return redirect('lista_ordini')

@login_required
def conferma_ordine(request, pk):
    ordine = get_object_or_404(Ordine, pk=pk)
    ordine.utente = request.user
    ordine.save()
    stato = get_object_or_404(Stato, chiave="in_preparazione")
    try:
        ordine.cambia_stato_righe(stato)
        messages.success(request, f"Ordine #{ordine.id}-{ordine.cliente} confermato con successo.")
    except prodottoError as e:
        messages.warning(request, f"Ordine #{ordine.id}-{ordine.cliente} {str(e)}")


    return redirect('lista_ordini')


@login_required
def evasione(request):
    data_ordine = request.GET.get('data_ordine')
    data_ordine, data_precedente, data_successiva = ottieni_data_ordine_precedente_successiva(data_ordine)
    sottocategorie_visualizzate = request.user.userprofile.postazione_predefinita.sottocategorie_associate.all()
    box_associati = request.user.userprofile.postazione_predefinita.box_associati.all()

    righe = OrdineRiga.objects.righe_da_evadere(data_ordine, stati_ordine=["in_preparazione", "pronto"], sottocategorie=sottocategorie_visualizzate)
    righe_raggruppate = OrdineRiga.objects.righe_raggruppate_per_categoria(righe)

    return render(request, 'ordini/evasione.html', {
        'righe_raggruppate': righe_raggruppate,
        'is_consegna': False,
        'box_liberi': ', '.join([i.valore for i in box_associati]),
        'sottocategorie_visualizzate': ', '.join([i.valore for i in sottocategorie_visualizzate]),
        'title': f"Ordini da evadere {data_ordine.strftime('%d-%m-%Y')}"
    })

@login_required
def consegne(request):
    if request.method == 'POST':
        riga_id = request.POST.get('riga_id')
        nuovo_stato = request.POST.get('nuovo_stato')

        riga = get_object_or_404(OrdineRiga, id=riga_id)
        riga.stato = nuovo_stato
        riga.utente = request.user
        riga.save()

        return redirect(request.path)  # ricarica la pagina

    sottocategorie_visualizzate = request.user.userprofile.postazione_predefinita.sottocategorie_associate.all()

    data_ordine = request.GET.get('data_ordine')
    data_ordine, data_precedente, data_successiva = ottieni_data_ordine_precedente_successiva(data_ordine)
    righe = OrdineRiga.objects.righe_da_evadere(data_ordine, stati_ordine=["pronto", "non_trovato"], sottocategorie=sottocategorie_visualizzate)
    righe_raggruppate = OrdineRiga.objects.righe_raggruppate_per_categoria(righe)

    return render(request, 'ordini/evasione.html', {
        'righe_raggruppate': righe_raggruppate,
        'is_consegna': True,
        'box_liberi': '',
        'sottocategorie_visualizzate': ', '.join([i.valore for i in sottocategorie_visualizzate]),
        'title': f"Ordini da consegnare {data_ordine.strftime('%d-%m-%Y')}",

    })

@login_required
def set_stato_riga_ordine(request, pk="", stato="", is_consegna=1):
    is_consegna = bool(is_consegna)
    riga = get_object_or_404(OrdineRiga, id=pk)
    nuovo_stato = get_object_or_404(Stato, chiave=stato)
    riga.stato = nuovo_stato
    riga.utente = request.user
    riga.save()
    # Recupera il parametro data_ordine, se presente
    data_ordine = request.GET.get('data_ordine')

    messages.success(request, f"Ordine #{riga.ordine.id}.{riga.id} passata in {riga.stato.valore}")

    if is_consegna:
        # Costruisci l’URL con il parametro
        url = reverse('consegne')
    else:
        url = reverse('evasione')

    if data_ordine:
        url += f"?data_ordine={data_ordine}"
    return redirect(url)



def ottieni_data_ordine_precedente_successiva(data_ordine, stati_ammessi=[]):
    if not data_ordine:
        data_ordine = localdate()    # restituisce la data odierna (timezone aware)
    else:
        data_ordine = datetime.strptime(data_ordine, '%d-%m-%Y')

    # Filtro per stato se fornito
    ordini_qs = Ordine.objects.all()
    if stati_ammessi:
        ordini_qs = ordini_qs.filter(stato__in=stati_ammessi)

    date_distinte = ordini_qs.annotate(data=TruncDate('creato')) \
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