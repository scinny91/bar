
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("cassa/", views.cassa, name="cassa"),
    path("cucina/", views.cucina, name="cucina"),
    path('', include('bar.prodotti.urls')),
    path('', include('bar.ordini.urls')),
]
