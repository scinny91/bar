from django.db import models

from bar.core import Categoria, Sottocategoria

CATEGORIE_PRODOTTO = Categoria.get_choices(with_void=False)
SOTTOCATEGORIE_PRODOTTO = Sottocategoria.get_choices(with_void=False)

class Prodotto(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    prezzo = models.DecimalField(max_digits=6, decimal_places=2)
    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.SET_NULL,  # se la sottocategoria viene cancellata, metto null
        null=True,  # permette valore null
        blank=True,
    )
    sottocategoria = models.ForeignKey(
        'Sottocategoria',
        on_delete=models.SET_NULL,  # se la sottocategoria viene cancellata, metto null
        null=True,  # permette valore null
        blank=True,
    )
    def __str__(self):
        cat = self.categoria.valore if self.categoria else "Senza categoria"
        sub = self.sottocategoria.valore if self.sottocategoria else "Senza sottocategoria"
        return f"{self.nome} ({cat} / {sub}) - €{self.prezzo}"


