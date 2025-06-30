from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models

CATEGORIE_PRODOTTO = [
    ("bar", "bar"),
    ("cucina", "cucina"),
]
SOTTOCATEGORIE_PRODOTTO = [
    ("patatine", "patatine"),
    ("piastra", "piastra"),
    ("special", "special"),
    ("affettato", "affettato"),
    ("gnocco", "gnocco"),
    ("", "-"),
]

class Prodotto(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    prezzo = models.DecimalField(max_digits=6, decimal_places=2)
    categoria = models.CharField(max_length=50, choices=CATEGORIE_PRODOTTO, default='bar')
    sottocategoria = models.CharField(max_length=50, blank=True, null=True, choices=SOTTOCATEGORIE_PRODOTTO)
    def __str__(self):
        return self.nome
