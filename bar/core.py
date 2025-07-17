from django.db import models

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

class Sottocategoria(ParametroGenerico):
    pass