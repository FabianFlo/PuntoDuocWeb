from django.urls import path
from .views import crear_encuesta, ver_encuestas, responder_encuesta

urlpatterns = [
    path('crear/', crear_encuesta, name='crear_encuesta'),
    path('ver/', ver_encuestas, name='ver_encuestas'),
    path('responder/<str:encuesta_id>/', responder_encuesta, name='responder_encuesta'),  # Cambiado a str para ID
]
