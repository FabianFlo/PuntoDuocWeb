from django.urls import path
from .views import index, subir_evento_view

urlpatterns = [
    path('', index, name='index'),
    path('subir_evento/', subir_evento_view, name='subir_evento'),  # Cambia la ruta aquí
]
