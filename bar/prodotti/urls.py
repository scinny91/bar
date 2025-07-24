from django.urls import path
from . import views

urlpatterns = [
    path('magazzino/giacenze/', views.aggiorna_giacenze, name='aggiorna_giacenze'),
]