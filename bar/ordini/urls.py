
from django.urls import path
from . import views

urlpatterns = [
    path('ordini/', views.lista_ordini, name='lista_ordini'),
    path('ordini/nuovo/', views.nuovo_ordine, name='nuovo_ordine'),
    path('ordini/<int:pk>/modifica/', views.modifica_ordine, name='modifica_ordine'),
    path('ordini/<int:pk>/elimina/', views.elimina_ordine, name='elimina_ordine'),
    path('ordini/<str:categoria>/', views.evasione, name='evasione'),
]

