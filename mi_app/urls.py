from django.urls import path
from .views import *

urlpatterns = [
    path('subir_evento/', subir_evento_view, name='subir_evento'),
    path('listar_eventos/', listar_eventos_view, name='listar_eventos'),
    path('eliminar_evento/<str:evento_id>/', eliminar_evento_view, name='eliminar_evento'),
    path('modificar_evento/<str:evento_id>/', modificar_evento_view, name='modificar_evento'),
    path('', home_view, name='home'),  # Ruta para el home page
    path('crear_estudiante/', crear_estudiante_view, name='crear_estudiante'),
    path('listar_estudiantes/', listar_estudiantes_view, name='listar_estudiantes'),
    path('eliminar_estudiante/<str:estudiante_id>/', eliminar_estudiante_view, name='eliminar_estudiante'),
     path('modificar_estudiante/<str:estudiante_id>/', modificar_estudiante_view, name='modificar_estudiante'),
]
