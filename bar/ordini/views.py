from collections import defaultdict
from django.utils.timezone import localdate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from bar.ordini.models import Ordine, OrdineRiga, STATUS_CHOICES, OPTION_CHOICES
from bar.prodotti.models import Prodotto, CATEGORIE_PRODOTTO, SOTTOCATEGORIE_PRODOTTO


@login_required
def nuovo_ordine(request):
    prodotti = Prodotto.objects.all().order_by('categoria', 'sottocategoria', 'nome')
    if request.method == 'POST':
        # Leggi quantità inviate (qty_<id>)
        ordine = Ordine.objects.create(stato='in_attesa')  # stato iniziale

        for prodotto in prodotti:
            qty = request.POST.get(f'qty_{prodotto.id}', '0')
            try:
                qty = int(qty)
            except ValueError:
                qty = 0

            if qty > 0:
                OrdineRiga.objects.create(
                    ordine=ordine,
                    prodotto=prodotto,
                    quantita=qty,
                    stato='in_attesa'
                )
        return redirect('lista_ordini')  # o altra pagina di conferma
    context = {
        'titolo_pagina': 'Nuovo Ordine',
        'bottone_submit': 'Inserisci Ordine',
        'quantità': {},  # vuoto all'inizio
        'nome_ordine': '',
        'prodotti': prodotti,
        'opzioni': OPTION_CHOICES,
        'is_new': True
    }
    return render(request, 'ordini/ordine_form.html', context)

@login_required
def lista_ordini(request):
    oggi = localdate()  # restituisce la data odierna (timezone aware)
    ordini = Ordine.objects.filter(creato__date=oggi).order_by('creato')

    totali = {}
    for stato_ordine in STATUS_CHOICES:
        totali[stato_ordine[0]] = {}
        for categoria in CATEGORIE_PRODOTTO:
            totali[stato_ordine[0]][categoria[0]] = {}
            for sottocategoria in SOTTOCATEGORIE_PRODOTTO:
                totali[stato_ordine[0]][categoria[0]][sottocategoria[0]] = {
                    "quantità": 0,
                    "totale": 0
                }

    for ordine in ordini:
        stato = ordine.stato
        for riga in ordine.items.all():
            cat = riga.prodotto.categoria
            sottocat = riga.prodotto.sottocategoria

            qta = riga.quantita
            prezzo = float(riga.prodotto.prezzo)
            tot = qta * prezzo

            totali[stato][cat][sottocat]["quantità"] += qta
            totali[stato][cat][sottocat]["totale"] += tot

    context = { "ordini": ordini,
                "totali_per_stato_cat_sottocat": totali,
    }

    return render(request, "ordini/lista_ordini.html", context)


@login_required
def modifica_ordine(request, pk):
    ordine = get_object_or_404(Ordine, id=pk)
    prodotti = Prodotto.objects.all().order_by('categoria', 'sottocategoria', 'nome')

    if request.method == 'POST':
        ordine.cliente = request.POST.get('nome_ordine', '')
        ordine.save()
        ordine.items.all().delete()

        for prodotto in prodotti:
            qty_list = request.POST.getlist(f'qty_{prodotto.id}[]')
            opt_list = request.POST.getlist(f'opt_{prodotto.id}[]')

            for qty_str, opt in zip(qty_list, opt_list):
                try:
                    qty = int(qty_str)
                except ValueError:
                    qty = 0

                if qty > 0:
                    OrdineRiga.objects.create(
                        ordine=ordine,
                        prodotto=prodotto,
                        quantita=qty,
                        stato='in_attesa',
                        opzioni=opt
                    )

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
    if request.method == 'POST':
        ordine.delete()
        return redirect('lista_ordini')


@login_required
def evasione(request, categoria):
    righe = OrdineRiga.objects.select_related('ordine', 'prodotto') \
        .filter(stato='in_attesa', prodotto__categoria=categoria) \
        .order_by('ordine__creato')

    return render(request, 'ordini/evasione.html', {
        'categoria': categoria,
        'righe': righe,
    })