from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from datetime import date
from bar.ordini.models import Ordine, OrdineRiga
from django.contrib.auth.decorators import login_required


@login_required
def riepilogo_bilancio(request):
    # Recupera tutte le date disponibili in Ordine
    chart_type = request.GET.get('chart_type', 'bar')  # default = bar

    available_dates_qs = OrdineRiga.objects.values_list("ordine__creato__date", flat=True).distinct().order_by(
        "ordine__creato__date")
    available_dates = sorted(set(d.strftime('%Y-%m-%d') for d in available_dates_qs))

    selected_dates = request.GET.getlist('dates')
    aggregation = request.GET.get('aggregation', 'categoria')
    chart_data_ricavi = None
    chart_data_costi = None
    redditivita = None

    if selected_dates:
        righe = OrdineRiga.objects.filter(ordine__creato__date__in=selected_dates)


        # Calcolo valore riga = quantita * prezzo
        righe = righe.annotate(
            ricavo=ExpressionWrapper(
                F('quantita') * F('prodotto__prezzo'),
                output_field=DecimalField()
            ),
            costo=ExpressionWrapper(
                F('quantita') * F('prodotto__componenti_magazzino__costo_acquisto'),
                output_field=DecimalField()
            ),
            quantita_totale=ExpressionWrapper(
                F('quantita'),
                output_field=DecimalField()
            ),
        )

        ricavo_totale = righe.aggregate(totale=Sum('ricavo'))['totale'] or 0
        costo_totale = righe.aggregate(totale=Sum('costo'))['totale'] or 0

        # Aggregazione dinamica per valore
        if aggregation == "categoria":
            ricavi = righe.values("prodotto__categoria__valore").annotate(totale=Sum("ricavo"))
            costi = righe.values("prodotto__categoria__valore").annotate(totale=Sum("costo"))
            quantita = righe.values("prodotto__categoria__valore").annotate(totale=Sum("quantita_totale"))
            labels = [r["prodotto__categoria__valore"] or "N/D" for r in ricavi]
        elif aggregation == "sottocategoria":
            ricavi = righe.values("prodotto__sottocategoria__valore").annotate(totale=Sum("ricavo"))
            costi = righe.values("prodotto__sottocategoria__valore").annotate(totale=Sum("costo"))
            quantita = righe.values("prodotto__sottocategoria__valore").annotate(totale=Sum("quantita_totale"))
            labels = [r["prodotto__sottocategoria__valore"] or "N/D" for r in ricavi]
        else:  # prodotto
            ricavi = righe.values("prodotto__nome").annotate(totale=Sum("ricavo"))
            costi = righe.values("prodotto__nome").annotate(totale=Sum("costo"))
            quantita = righe.values("prodotto__nome").annotate(totale=Sum("quantita_totale"))
            labels = [r["prodotto__nome"] for r in ricavi]

        redditivita = {}

        values = [float(r["totale"]) for r in ricavi]  # Per Chart.js
        for i in ricavi:
            redditivita[i["prodotto__nome"]] = {"key": i["prodotto__nome"],
                                                "attivo": i["totale"],
                                                "redditivita_attiva": i["totale"] / ricavo_totale *100,
                                                }
        chart_data_ricavi = {"labels": labels, "values": values}

        values = [float(r["totale"]) for r in costi]  # Per Chart.js
        chart_data_costi = {"labels": labels, "values": values}

        for i in costi:
            redditivita[i["prodotto__nome"]]["passivo"] = i["totale"]
            redditivita[i["prodotto__nome"]]["redditivita_passiva"] = i["totale"] / costo_totale *100
        for i in quantita:
            redditivita[i["prodotto__nome"]]["quantita_totale"] = i["totale"]



    return render(request, "bilancio/riepilogo_grafico.html", {
        "available_dates": available_dates,
        "selected_dates": selected_dates,
        "aggregation": aggregation,
        "chart_ricavi": chart_data_ricavi,
        "chart_costi": chart_data_costi,
        "chart_type": chart_type,
        "redditivita": redditivita,
    })

