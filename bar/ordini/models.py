from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from bar.prodotti.models import Prodotto

STATUS_CHOICES = [
        ('in_attesa', 'In Attesa'),
        ('in_preparazione', 'In Preparazione'),
        ('completato', 'Completato'),
    ]

OPTION_CHOICES = [
        ('cipolla', 'Cipolla'),
        ('peperoni', 'Peperoni'),
        ('cipolla&peperoni', 'Cipolla e peperoni'),
        ('asperto', 'Asporto'),
        ('meta', 'Taglia a metà'),
    ]



class Ordine(models.Model):

    id = models.AutoField(primary_key=True)
    creato = models.DateTimeField(auto_now_add=True)
    stato = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_attesa')
    cliente = models.CharField(max_length=40)

    def totale(self):
        return sum(item.totale() for item in self.items.all())

    def aggiorna_stato(self):
        stati = set(self.items.values_list('stato', flat=True))

        if stati == {'in_attesa'}:
            self.stato = 'in_attesa'
        elif stati == {'completato'}:
            self.stato = 'completato'
        else:
            self.stato = 'in_preparazione'

        self.save()

    def __str__(self):
        return f"Ordine {self.id} - {self.stato}"

class OrdineRiga(models.Model):
    id = models.AutoField(primary_key=True)
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='items')
    prodotto = models.ForeignKey(Prodotto, on_delete=models.CASCADE)
    quantita = models.PositiveIntegerField()
    stato = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_attesa')
    opzioni =  models.CharField(max_length=20, choices=OPTION_CHOICES, default='')



    def totale(self):
        return self.quantita * self.prodotto.prezzo

    def __str__(self):
        return f"{self.quantita}x {self.prodotto.nome}"

