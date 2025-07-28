from django.contrib.auth.models import User
from django.db import models
from bar.prodotti.models import Prodotto, CATEGORIE_PRODOTTO, SOTTOCATEGORIE_PRODOTTO, ComponenteMagazzino, prodottoError
from bar.core import Stato, Opzione
from collections import defaultdict


from itertools import groupby



STATUS_CHOICES = Stato.get_choices(with_void=False)
OPTION_CHOICES = Opzione.get_choices()


class OrdineRigaManager(models.Manager):
    def righe_raggruppate_per_categoria(self, righe):
        def safe_key(r):
            cat = r.prodotto.categoria.valore if r.prodotto.categoria else "Senza categoria"
            sub = r.prodotto.sottocategoria.valore if r.prodotto.sottocategoria else "Senza sottocategoria"
            return (cat, sub)

        righe_ordinate = sorted(righe, key=safe_key)
        raggruppate = []
        for key, chunk in groupby(righe_ordinate, key=safe_key):
            raggruppate.append({
                "categoria": key[0],
                "sottocategoria": key[1],
                "righe_ordini": list(chunk)
            })
        return raggruppate

    def righe_da_evadere(self, data_ordine, stati_ordine=[]):
        filtro_base = {
            'ordine__creato__date': data_ordine
        }
        if stati_ordine:
            filtro_base['stato__chiave__in'] = stati_ordine
        else:
            filtro_base['stato__chiave'] = 'in_attesa'  # default

        return self.select_related('ordine', 'prodotto') \
            .filter(**filtro_base) \
            .order_by('ordine__creato')

class Ordine(models.Model):

    id = models.AutoField(primary_key=True)
    creato = models.DateTimeField(auto_now_add=True)
    stato = models.ForeignKey(
        'Stato',
        on_delete=models.DO_NOTHING,  # se la sottocategoria viene cancellata, metto null
        null=True,  # permette valore null
        blank=True,
    )
    cliente = models.CharField(max_length=40)
    utente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


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

    def modifica_da_post_request(self, post_data, prodotti):
        """
        Crea le righe dell'ordine partendo dai dati POST e dai prodotti disponibili.
        Funziona sia che con un ordine vuoto che con un ordine da modificare
        """
        self.cliente = post_data.get('nome_ordine', '')
        self.save()

        #Ripristina giacenza se era stata scalata (in_preparazione o completato)
        for item in self.items.select_related('prodotto'):
            if item.stato.chiave in ("completato", "in_preparazione"):
                componenti = ComponenteMagazzino.objects.filter(prodotto=item.prodotto)
                for componente in componenti.select_related('magazzino'):
                    da_ripristinare = componente.quantita_totale_per(item.quantita)
                    componente.magazzino.quantita = models.F('quantita') + da_ripristinare
                    componente.magazzino.save()

        self.items.all().delete()

        for prodotto in prodotti:
            qty_list = post_data.getlist(f'qty_{prodotto.id}[]')
            opt_list = post_data.getlist(f'opt_{prodotto.id}[]')

            for qty_str, opt in zip(qty_list, opt_list):
                try:
                    qty = int(qty_str)
                except ValueError:
                    qty = 0

                if qty > 0:
                    obj = OrdineRiga.objects.create(
                        ordine=self,
                        prodotto=prodotto,
                        quantita=qty,
                        stato=Stato.objects.get(chiave="in_attesa"),
                    )

                    if opt:
                        obj.opzioni = Opzione.objects.get(chiave=opt)
                        obj.save()

    def cambia_stato_righe(self, new_stato):
        stato_completato = Stato.objects.get(chiave="completato")
        for item in self.items.all():
            # Se stiamo passando in "in_preparazione", scala le giacenze (se necessario)
            if new_stato.chiave == "in_preparazione":
                if item.prodotto.componenti_magazzino.exists() and item.stato.chiave not in ("in_preparazione", "completato"):
                    componenti = ComponenteMagazzino.objects.filter(prodotto=item.prodotto).select_related('magazzino')
                    for componente in componenti:
                        da_scalare = componente.quantita_totale_per(item.quantita)

                        if componente.magazzino.quantita < da_scalare and componente.bloccante:
                            raise prodottoError(f"Scorte insufficienti per {componente.magazzino.nome}")

                        componente.magazzino.quantita = models.F('quantita') - da_scalare
                        componente.magazzino.save()

            if new_stato.chiave == "in_preparazione" and item.prodotto.categoria.chiave != "cucina":
                # il bar va direttamente in completato
                item.stato = stato_completato
            else:
                item.stato = new_stato
            item.save()


    @staticmethod
    def calcola_totali(ordini):
        def defaultdict_to_dict(d):
            if isinstance(d, defaultdict):
                return {k: defaultdict_to_dict(v) for k, v in d.items()}
            return d

        def nested_dict():
            return defaultdict(nested_dict)

        totali = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"quantità": 0, "totale": 0})))

        for ordine in ordini:
            stato = ordine.stato.valore
            for riga in ordine.items.all():
                cat = riga.prodotto.categoria.valore if riga.prodotto.categoria else "Senza categoria"
                sub = riga.prodotto.sottocategoria.valore if riga.prodotto.sottocategoria else "Senza sottocategoria"

                qta = riga.quantita
                prezzo = float(riga.prodotto.prezzo)
                tot = qta * prezzo

                totali[stato][cat][sub]["quantità"] += qta
                totali[stato][cat][sub]["totale"] += tot

        totali = defaultdict_to_dict(totali)
        return totali


class OrdineRiga(models.Model):
    id = models.AutoField(primary_key=True)
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='items')
    prodotto = models.ForeignKey(Prodotto, on_delete=models.CASCADE)
    quantita = models.PositiveIntegerField()
    utente = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


    objects = OrdineRigaManager()

    stato = models.ForeignKey(
        'Stato',
        on_delete=models.DO_NOTHING,  # se la sottocategoria viene cancellata, metto null
        null=True,  # permette valore null
        blank=True,
    )
    opzioni = models.ForeignKey(
        'Opzione',
        on_delete=models.DO_NOTHING,  # se la sottocategoria viene cancellata, metto null
        null=True,  # permette valore null
        blank=True,
    )

    @property
    def opzioni_display(self):
        return self.opzioni.valore if self.opzioni else "Nessuna Opzione"

    def totale(self):
        return self.quantita * self.prodotto.prezzo

    def __str__(self):
        if self.opzioni:
            return f"{self.quantita}x {self.prodotto.nome} + {self.opzioni.valore}"
        return f"{self.quantita}x {self.prodotto.nome}"


