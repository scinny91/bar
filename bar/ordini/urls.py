
from django.urls import path
from . import views

urlpatterns = [
    path('ordini/inserimento/', views.lista_ordini, name='lista_ordini'),
    path('ordini/inserimento/nuovo/', views.nuovo_ordine, name='nuovo_ordine'),
    path('ordini/inserimento/<int:pk>/modifica/', views.modifica_ordine, name='modifica_ordine'),
    path('ordini/inserimento/<int:pk>/elimina/', views.elimina_ordine, name='elimina_ordine'),
    path('ordini/inserimento/<int:pk>/conferma/', views.conferma_ordine, name='conferma_ordine'),
    path('ordini/evasione/', views.evasione, name='evasione'),
    path('ordini/consegne/', views.consegne, name='consegne'),
    path('ordini/consegne/riga/<int:pk>/<str:stato>/<int:is_consegna>', views.set_stato_riga_ordine, name='set_stato_riga_ordine'),
    path('ordini/riepilogo/', views.riepilogo_ordini, name='riepilogo_ordini'),
    path('dashboard/', views.dashboard, name='dashboard'),
]

