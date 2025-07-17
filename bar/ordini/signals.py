from django.db.models.signals import post_save
from django.dispatch import receiver
from bar.ordini.models import OrdineRiga
from bar.core import Stato

@receiver(post_save, sender=OrdineRiga)
def aggiorna_stato_ordine(sender, instance, **kwargs):
    ordine = instance.ordine
    righe = ordine.items.all()

    stati = set(r.stato.chiave for r in righe)

    if stati == {'in_attesa'}:
        nuovo_stato = Stato.objects.get(chiave='in_attesa')
    elif stati == {'completato'}:
        nuovo_stato = Stato.objects.get(chiave='completato')
    else:
        nuovo_stato = Stato.objects.get(chiave='in_preparazione')

    if ordine.stato != nuovo_stato:
        ordine.stato = nuovo_stato
        ordine.save()