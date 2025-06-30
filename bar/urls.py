
from django.urls import path
from . import views

urlpatterns = [
    path("", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("cassa/", views.cassa, name="cassa"),
    path("cucina/", views.cucina, name="cucina"),
]
