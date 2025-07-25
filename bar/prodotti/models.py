from django.db import models
from django.core.validators import MinValueValidator

from bar.core import Categoria, Sottocategoria

CATEGORIE_PRODOTTO = Categoria.get_choices(with_void=False)
SOTTOCATEGORIE_PRODOTTO = Sottocategoria.get_choices(with_void=False)

class MagazzinoManager(models.Manager):
    def aggiorna_o_crea(self, nome, quantita, soglia_minima=0):
        nome = nome.strip()
        if not nome:
            raise ValueError("Il nome del magazzino non può essere vuoto.")

        try:
            quantita = int(quantita)
            soglia_minima = int(soglia_minima)
        except (TypeError, ValueError):
            raise ValueError("Quantità non valida.")

        obj, creato = self.get_or_create(nome__iexact=nome, defaults={'nome': nome})

        obj.quantita = quantita
        obj.soglia_minima = soglia_minima
        obj.save()

        return obj, creato

class Magazzino(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    quantita = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    soglia_minima = models.PositiveIntegerField(default=0)

    objects = MagazzinoManager()

    def __str__(self):
        return f"{self.nome} ({self.quantita})"

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
    componenti_magazzino = models.ManyToManyField(
        Magazzino,
        through='ComponenteMagazzino',
        related_name='distinta_base'
    )
    def __str__(self):
        cat = self.categoria.valore if self.categoria else "Senza categoria"
        sub = self.sottocategoria.valore if self.sottocategoria else "Senza sottocategoria"
        return f"{self.nome} ({cat} / {sub}) - €{self.prezzo}"

class ComponenteMagazzino(models.Model):
    prodotto = models.ForeignKey(Prodotto, on_delete=models.CASCADE)
    magazzino = models.ForeignKey(Magazzino, on_delete=models.CASCADE)
    quantita_utilizzata = models.FloatField()  # quantità base per 1 unità di prodotto
    percentuale_maggiorazione = models.FloatField(default=0)  # es: 10 per +10%
    bloccante = models.BooleanField(default=True, help_text="Se attivo, l'esaurimento blocca la preparazione")


    def quantita_totale_per(self, quantita_prodotto):
        base = self.quantita_utilizzata * quantita_prodotto
        maggiorazione = base * (self.percentuale_maggiorazione / 100)
        return base + maggiorazione
    def rapr_per_anagrafica(self):
        return f"{self.magazzino.nome}: {self.quantita_utilizzata} + {self.percentuale_maggiorazione}% "
    def __str__(self):
        return f"{self.prodotto.nome} consuma {self.quantita_utilizzata} + {self.percentuale_maggiorazione}% di {self.magazzino.nome}"