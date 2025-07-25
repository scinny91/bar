from django.urls import path
from . import views

urlpatterns = [
    path('magazzino/giacenze/', views.aggiorna_giacenze, name='aggiorna_giacenze'),
    path('anagrafica-prodotti/<int:prodotto_id>/', views.modifica_prodotto, name='modifica_prodotto'),
    path('anagrafica-prodotti/', views.elenco_anagrafiche_prodotti, name='elenco_anagrafiche_prodotti'),

]