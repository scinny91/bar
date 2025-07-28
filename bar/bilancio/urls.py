
from django.urls import path
from . import views

urlpatterns = [
    path('bilancio/', views.riepilogo_bilancio, name='riepilogo_bilancio'),
]

