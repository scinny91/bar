from django.db.models.signals import post_save
from django.dispatch import receiver
from bar.ordini.models import OrdineRiga
from bar.core import Stato

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