from django.db.models.signals import post_save
from django.dispatch import receiver
from bar.ordini.models import OrdineRiga, BoxAllocazione
from bar.core import Stato, Box, Postazione



@receiver(post_save, sender=OrdineRiga)
def aggiorna_stato_ordine(sender, instance, **kwargs):
    ordine = instance.ordine
    #righe = ordine.items.all()
    #stati = set(r.stato.chiave for r in righe if not r.prodotto.sottocategoria.flag_subito_completato)
    # flag_subito_completato li devo escludere, passano sempre in confermato e porterebbero sempre lo stato su misto/completo
    righe = ordine.items.select_related(
        'stato',
        'prodotto__sottocategoria'
    )

    stati = {
        r.stato.chiave
        for r in righe
        if not r.prodotto.sottocategoria.flag_subito_completato
    }

    if not stati:
        # se ho solo flag_subito_completato, sono già tutti completati
        nuovo_stato = Stato.objects.get(chiave='completato')
    elif stati == {'in_attesa'}:
        nuovo_stato = Stato.objects.get(chiave='in_attesa')
    elif stati == {'completato'}:
        nuovo_stato = Stato.objects.get(chiave='completato')
    elif stati == {'pronto'}:
        nuovo_stato = Stato.objects.get(chiave='pronto')
    elif ('in_preparazione' in stati or 'pronto' in stati) and 'completato' in stati:
        # caso misto
        nuovo_stato = Stato.objects.get(chiave='parzialmente_completato')
    else:
        nuovo_stato = Stato.objects.get(chiave='in_preparazione')

    if ordine.stato != nuovo_stato:
        ordine.stato = nuovo_stato
        ordine.save()

    stato_corrente = instance.stato.chiave

    if stato_corrente == 'pronto':
        postazione = instance.prodotto.sottocategoria.postazione
        # Se non c'è un box attivo per questa coppia, lo creo
        if not BoxAllocazione.objects.filter(
                ordine=ordine, postazione=postazione, attivo=True
        ).exists():
            box_libero = postazione.box_associati.filter(attivo=False).first()

            if not box_libero:
                # Se non c'è, creo un box nuovo (oppure puoi lanciare errore)
                box_libero = Box.objects.create(
                    codice=f"BOX-{Box.objects.count() + 1}", attivo=True
                )
            else:
                box_libero.attivo = True
                box_libero.save()

            BoxAllocazione.objects.create(
                ordine=ordine,
                postazione=postazione,
                box=box_libero,
                attivo=True
            )

        # --- LIBERAZIONE ---
    if stato_corrente == 'completato':
        if instance.prodotto.sottocategoria.flag_subito_completato == False:
            postazione = instance.prodotto.sottocategoria.postazione
            righe_postazione = ordine.items.filter(
                prodotto__sottocategoria__postazione=postazione
            )
            if all(r.stato.chiave == 'completato' for r in righe_postazione):

                # Trovo l'allocazione attiva e la libero
                alloc = BoxAllocazione.objects.filter(
                    ordine=ordine, postazione=postazione, attivo=True
                ).first()
                if alloc:
                    alloc.attivo = False
                    alloc.save()
                    # Libero fisicamente il box
                    alloc.box.attivo = False
                    alloc.box.save()
