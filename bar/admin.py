from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin, ImportMixin, ImportExportModelAdmin
from bar.prodotti.models import Prodotto, Magazzino, ComponenteMagazzino
from bar.ordini.models import Ordine, OrdineRiga
from bar.core import Stato, Opzione, Categoria, Sottocategoria


# Classe generica per i resource
class GenericResource(resources.ModelResource):
    class Meta:
        model = None  # da sovrascrivere dinamicamente

# Classe admin riutilizzabile
class BaseImportExportAdmin(ImportExportModelAdmin):
    def get_resource_class(self):
        class Meta:
            model = self.model
        resource_class = type(f"{self.model.__name__}Resource", (resources.ModelResource,), {"Meta": Meta})
        return resource_class



@admin.register(Ordine)
class OrdineAdmin(BaseImportExportAdmin):
    pass

@admin.register(OrdineRiga)
class OrdineRigaAdmin(BaseImportExportAdmin):
    pass

@admin.register(Prodotto)
class ProdottoAdmin(BaseImportExportAdmin):
    pass

@admin.register(Magazzino)
class MagazzinoAdmin(BaseImportExportAdmin):
    pass

@admin.register(ComponenteMagazzino)
class ComponenteMagazzinoAdmin(BaseImportExportAdmin):
    pass

@admin.register(Stato)
class StatoAdmin(BaseImportExportAdmin):
    pass

@admin.register(Opzione)
class OpzioneAdmin(BaseImportExportAdmin):
    pass

@admin.register(Categoria)
class CategoriaAdmin(BaseImportExportAdmin):
    pass

@admin.register(Sottocategoria)
class SottocategoriaAdmin(BaseImportExportAdmin):
    pass