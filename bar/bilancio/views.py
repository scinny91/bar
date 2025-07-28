from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from datetime import date
from bar.ordini.models import Ordine, OrdineRiga
from django.contrib.auth.decorators import login_required
from decimal import Decimal



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
                F('quantita') * F('prodotto__componenti_magazzino__costo_acquisto') * F('prodotto__componentemagazzino__quantita_utilizzata'),
                output_field=DecimalField()
            ),
            quantita_totale=ExpressionWrapper(
                F('quantita'),
                output_field=DecimalField()
            ),
        )

        ricavo_totale = righe.aggregate(totale=Sum('ricavo'))['totale'] or 0
        costo_totale = righe.aggregate(totale=Sum('costo'))['totale'] or 0

        # Aggregazione dinamica
        if aggregation == "categoria":
            chiave = "prodotto__categoria__valore"
        elif aggregation == "sottocategoria":
            chiave = "prodotto__sottocategoria__valore"
        else:
            chiave = "prodotto__nome"

        ricavi = righe.values(chiave).annotate(totale=Sum("ricavo"))
        quantita = righe.values(chiave).annotate(totale=Sum("quantita_totale"))
        costi = righe.values(chiave).annotate(totale=Sum("costo"))
        labels = [r[chiave] or "N/D" for r in ricavi]




        values = [float(r["totale"]) for r in ricavi]  # Per Chart.js
        chart_data_ricavi = {"labels": labels, "values": values}

        values = [float(r["totale"]) for r in costi]  # Per Chart.js
        chart_data_costi = {"labels": labels, "values": values}

        redditivita = []

        for label in labels:
            attivo = next((r["totale"] for r in ricavi if (r[chiave] or "N/D") == label), Decimal('0'))
            passivo = next((r["totale"] for r in costi if (r[chiave] or "N/D") == label), Decimal('0'))
            quant = next((q["totale"] for q in quantita if (q[chiave] or "N/D") == label), 0)

            redditivita.append({
                "chiave": label,
                "attivo": attivo,
                "perc_attivo": (attivo / ricavo_totale * 100) if ricavo_totale else 0,
                "passivo": passivo,
                "perc_passivo": (passivo / costo_totale * 100) if costo_totale else 0,
                "quantita_totale": quant,
                "utile": (attivo - passivo),
            })



    return render(request, "bilancio/riepilogo_grafico.html", {
        "available_dates": available_dates,
        "selected_dates": selected_dates,
        "aggregation": aggregation,
        "chart_ricavi": chart_data_ricavi,
        "chart_costi": chart_data_costi,
        "chart_type": chart_type,
        "redditivita": redditivita,
    })

