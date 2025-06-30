from django.db.models.signals import post_save
from django.dispatch import receiver
from bar.ordini.models import OrdineRiga

@receiver(post_save, sender=OrdineRiga)
def aggiorna_stato_ordine(sender, instance, **kwargs):
    ordine = instance.ordine
    righe = ordine.items.all()

    stati = set(r.stato for r in righe)

    if stati == {'in_attesa'}:
        ordine.stato = 'in_attesa'
    elif stati == {'completato'}:
        ordine.stato = 'completato'
    else:
        ordine.stato = 'in_preparazione'

    ordine.save()