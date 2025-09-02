from django.contrib.auth.models import User
from django.db import transaction
from django.db import models
from django.core.cache import cache

from bar.prodotti.models import Prodotto, CATEGORIE_PRODOTTO, SOTTOCATEGORIE_PRODOTTO, ComponenteMagazzino, prodottoError
from bar.core import Stato, Opzione, Box, Postazione

from itertools import groupby
from collections import Counter




STATUS_CHOICES = Stato.get_choices(with_void=False)
OPTION_CHOICES = Opzione.get_choices()


class OrdineRigaManager(models.Manager):
    def righe_raggruppate_per_categoria(self, righe):
        def safe_key(r):
            cat = r.prodotto.sottocategoria.categoria.valore if r.prodotto.sottocategoria.categoria else "Senza categoria"
            sub = r.prodotto.sottocategoria.valore if r.prodotto.sottocategoria else "Senza sottocategoria"
            return (cat, sub)

        righe_ordinate = sorted(righe, key=safe_key)
        raggruppate = []
        for key, chunk in groupby(righe_ordinate, key=safe_key):
            l = list(sorted(chunk, key= lambda x: x.ordine.id))

            raggruppate.append({
                "categoria": key[0],
                "sottocategoria": key[1],
                "righe_ordini": l
            })
        return raggruppate

    def righe_da_evadere(self, data_ordine, stati_ordine=None, sottocategorie=None):
        filtro_base = {
            'ordine__creato__date': data_ordine
        }

        if stati_ordine:
            filtro_base['stato__chiave__in'] = stati_ordine
        else:
            filtro_base['stato__chiave'] = 'in_attesa'  # default

        if sottocategorie:
            filtro_base['prodotto__sottocategoria__in'] = sottocategorie

        prefetch_componenti = models.Prefetch(
            'prodotto__componentemagazzino_set',
            queryset=ComponenteMagazzino.objects.filter(bloccante=True),
            to_attr='componenti_bloccanti'
        )

        return (
            self.select_related(
                'ordine',
                'stato',
                'prodotto__sottocategoria__categoria'
            )
            .prefetch_related(prefetch_componenti)
            .filter(**filtro_base)
            .order_by('ordine__creato')
        )

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

        # Pre-fetch
        # Recupera lo stato, usando cache
        stato_in_attesa = cache.get("stato_in_attesa")
        if not stato_in_attesa:
            stato_in_attesa = Stato.objects.get(chiave="in_attesa")
            cache.set("stato_in_attesa", stato_in_attesa, timeout=3600)  # cache per 1h

        # Recupera tutte le opzioni in cache
        opzioni_dict = cache.get("opzioni_dict")
        if not opzioni_dict:
            opzioni_dict = {op.chiave: op for op in Opzione.objects.all()}
            cache.set("opzioni_dict", opzioni_dict, timeout=3600)

        righe_da_creare = []

        for prodotto in prodotti:
            qty_list = post_data.getlist(f'qty_{prodotto.id}[]')
            opt_list = post_data.getlist(f'opt_{prodotto.id}[]')

            for qty_str, opt_key in zip(qty_list, opt_list):
                try:
                    qty = int(qty_str)
                except ValueError:
                    qty = 0

                if qty > 0:
                    obj = OrdineRiga(
                        ordine=self,
                        prodotto=prodotto,
                        quantita=qty,
                        stato=stato_in_attesa,
                    )

                    # Associa opzione solo se esiste
                    if opt_key and opt_key in opzioni_dict:
                        obj.opzioni = opzioni_dict[opt_key]

                    righe_da_creare.append(obj)

        # Inserimento bulk
        with transaction.atomic():
            OrdineRiga.objects.bulk_create(righe_da_creare)

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

            if new_stato.chiave == "in_preparazione" and item.prodotto.sottocategoria.flag_subito_completato:
                # il bar va direttamente in completato
                item.stato = stato_completato
            else:
                item.stato = new_stato
            item.save()

    @staticmethod
    def calcola_da_preparare(righe_ordini):
        # prendo solo righe in preparazione
        righe_in_preparazione = (r for r in righe_ordini if r.stato and r.stato.chiave == "in_preparazione")
        # sommo quantità per prodotto
        conteggio = Counter()
        # per ogni componente di magazzino del prodotto ma solo per ciò che è bloccante
        for r in righe_in_preparazione:
            for comp in r.prodotto.componenti_bloccanti:  # già prefetched
                qta = comp.quantita_totale_per(r.quantita)
                conteggio[comp.magazzino.nome] += qta

        # genero lista finale, escludendo i totali = 0
        prodotti_in_preparazione = sorted(
            ((nome, int(totale)) for nome, totale in conteggio.items() if totale > 0),
            key=lambda x: x[0]
        )
        return prodotti_in_preparazione

    @staticmethod
    def calcola_totali(ordini):
        """
        ordini: QuerySet di ordini
        """
        stati_ordinati = [
            Stato.objects.get(chiave="in_attesa"),
            Stato.objects.get(chiave="in_preparazione"),
            Stato.objects.get(chiave="pronto"),
            Stato.objects.get(chiave="non_trovato"),
            Stato.objects.get(chiave="completato"),
        ]

        # struttura base con Stato come chiave
        struttura = {stato.chiave: {} for stato in stati_ordinati}

        # calcolo totali
        for ordine in ordini:
            for riga in ordine.items.all():
                chiave_stato = riga.stato.chiave
                cat = (
                    riga.prodotto.sottocategoria.categoria.valore
                    if riga.prodotto.sottocategoria and riga.prodotto.sottocategoria.categoria
                    else "Senza categoria"
                )
                sub = (
                    riga.prodotto.sottocategoria.valore
                    if riga.prodotto.sottocategoria
                    else "Senza sottocategoria"
                )

                qta = riga.quantita
                prezzo = float(riga.prodotto.prezzo)
                tot = qta * prezzo

                if cat not in struttura[chiave_stato]:
                    struttura[chiave_stato][cat] = {}
                if sub not in struttura[chiave_stato][cat]:
                    struttura[chiave_stato][cat][sub] = {"quantità": 0, "totale": 0}

                struttura[chiave_stato][cat][sub]["quantità"] += qta
                struttura[chiave_stato][cat][sub]["totale"] += tot

        # costruisco lista finale con stato.valore
        lista_finale = []
        for stato in stati_ordinati:
            chiave = stato.chiave
            lista_finale.append({
                "nome": stato.valore,           # qui uso il valore leggibile
                "categorie": [
                    {"nome": cat, "sottocategorie": struttura[chiave][cat]}
                    for cat in struttura[chiave]
                ]
            })

        return lista_finale


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

    def stampa_dettagli(self):
        if self.stato.chiave in ("completato", "non_trovato"):
            return f"{self.__str__()} [{self.stato.valore} da: {self.utente}]"
        return f"{self.__str__()}"

    def get_box(self):
        # Trova il box assegnato a ordine+postazione
        box = BoxAllocazione.objects.filter(
            postazione=self.prodotto.sottocategoria.postazione,
            ordine=self.ordine
        ).first()
        if box:
            return box.__str__()
        else:
            return "Nessun box"

class BoxAllocazione(models.Model):
    ordine = models.ForeignKey('Ordine', on_delete=models.CASCADE)
    postazione = models.ForeignKey('Postazione', on_delete=models.CASCADE)
    box = models.ForeignKey('Box', on_delete=models.CASCADE)
    attivo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ordine', 'postazione', 'attivo'],
                name='unique_active_box_per_postazione_ordine'
            )
        ]

    def __str__(self):
        return f"{self.box}"
        return f"{self.box} → Ordine {self.ordine.id} ({self.postazione})"