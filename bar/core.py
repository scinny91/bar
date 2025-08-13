from django.db import models
from django.contrib.auth.models import User
from django.template.defaulttags import comment

#from bar.ordini.models import Ordine

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    postazione_predefinita = models.ForeignKey(
        'Postazione',
        on_delete=models.SET_NULL,  # se la postazione viene cancellata, metto null
        null=True,  # permette valore null
        blank=True,
    )
    def __str__(self):
        return f"Profilo di {self.user.username}"

class ParametroGenerico(models.Model):
    chiave = models.CharField(max_length=50, unique=True)
    valore = models.CharField(max_length=100)

    class Meta:
        abstract = True

    @classmethod
    def get_choices(cls, with_void=True):
        try:
            qs = cls.objects.all().order_by('valore')
            choices = [(obj.chiave, obj.valore) for obj in qs]
            if with_void:
                choices.insert(0, ("", "-"))
            return choices
        except Exception:
            # fallback: lista vuota o una scelta di default
            return [("", "-")] if with_void else []


    def __str__(self):
        return self.valore

class Stato(ParametroGenerico):
    pass

class Opzione(ParametroGenerico):
    pass

class Categoria(ParametroGenerico):
    pass

class Postazione(ParametroGenerico):
    sottocategorie_associate = models.ManyToManyField('Sottocategoria', blank=True, related_name='sottocategorie_associate')
    pass



class Sottocategoria(ParametroGenerico):
    opzioni_abilitate = models.ManyToManyField('Opzione', blank=True, related_name='opzioni_abilitate')
    flag_subito_completato = models.BooleanField(default=False)

    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.SET_NULL,  # se la sottocategoria viene cancellata, metto null
        null=True,  # permette valore null
        blank=True,
    )

    def get_opzioni_abilitate_choices(self, with_void=True):
        try:
            qs = self.opzioni_abilitate.all().order_by('valore')
            choices = [(obj.chiave, obj.valore) for obj in qs]
            if with_void:
                choices.insert(0, ("", "nessuna opzione"))
            return choices
        except Exception:
            return [("", "-")] if with_void else []
    pass

class  Box(ParametroGenerico):
    is_free = models.BooleanField(default=True)
    postazione = models.ForeignKey(
        'Postazione',
        on_delete=models.SET_NULL,  # se la sottocategoria viene cancellata, metto null
        null=True,  # permette valore null
        blank=True,
    )
