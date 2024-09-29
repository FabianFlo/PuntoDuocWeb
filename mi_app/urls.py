from django.urls import path
from .views import *

urlpatterns = [
    path('subir_evento/', subir_evento_view, name='subir_evento'),
    path('listar_eventos/', listar_eventos_view, name='listar_eventos'),
    path('eliminar_evento/<str:evento_id>/', eliminar_evento_view, name='eliminar_evento'),
    path('modificar_evento/<str:evento_id>/', modificar_evento_view, name='modificar_evento'),

]
