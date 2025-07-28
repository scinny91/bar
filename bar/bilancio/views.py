from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from datetime import date
from bar.ordini.models import Ordine, OrdineRiga
from django.contrib.auth.decorators import login_required


@login_required
def riepilogo_bilancio(request):
    # Recupera tutte le date disponibili in Ordine
    available_dates_qs = OrdineRiga.objects.values_list("ordine__creato__date", flat=True).distinct().order_by(
        "ordine__creato__date")
    available_dates = sorted(set(d.strftime('%Y-%m-%d') for d in available_dates_qs))

    selected_dates = request.GET.getlist('dates')
    aggregation = request.GET.get('aggregation', 'categoria')
    chart_data = None

    if selected_dates:
        righe = OrdineRiga.objects.filter(ordine__creato__date__in=selected_dates)


        # Calcolo valore riga = quantita * prezzo
        righe = righe.annotate(
            valore=ExpressionWrapper(
                F('quantita') * F('prodotto__prezzo'),
                output_field=DecimalField()
            )
        )

        # Aggregazione dinamica per valore
        if aggregation == "categoria":
            dati = righe.values("prodotto__categoria__valore").annotate(totale=Sum("valore"))
            labels = [r["prodotto__categoria__valore"] or "N/D" for r in dati]
        elif aggregation == "sottocategoria":
            dati = righe.values("prodotto__sottocategoria__valore").annotate(totale=Sum("valore"))
            labels = [r["prodotto__sottocategoria__valore"] or "N/D" for r in dati]
        else:  # prodotto
            dati = righe.values("prodotto__nome").annotate(totale=Sum("valore"))
            labels = [r["prodotto__nome"] for r in dati]

        values = [float(r["totale"]) for r in dati]  # Per Chart.js
        chart_data = {"labels": labels, "values": values}


    return render(request, "bilancio/riepilogo_grafico.html", {
        "available_dates": available_dates,
        "selected_dates": selected_dates,
        "aggregation": aggregation,
        "chart_data": chart_data
    })

