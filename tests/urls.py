# tests/urls.py
from django.urls import include, path

urlpatterns = [
    path("coreagenda/", include("coreagenda.urls")),
]

