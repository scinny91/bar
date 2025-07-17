
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    #path('', include('bar.prodotti.urls')),
    path('', include('bar.ordini.urls')),
]
