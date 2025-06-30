
from django.urls import path
from . import views

urlpatterns = [
    path('prodotti/', views.lista_prodotti, name='lista_prodotti'),
    path('prodotti/nuovo/', views.nuovo_prodotto, name='nuovo_prodotto'),
    path('prodotti/<int:pk>/modifica/', views.modifica_prodotto, name='modifica_prodotto'),
    path('prodotti/<int:pk>/elimina/', views.elimina_prodotto, name='elimina_prodotto'),

]
