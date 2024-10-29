from django.urls import include, path
from .views import *
from django.urls import path
from . import views


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
    path('metricas/', metricas_view, name='metricas'),
    path('metricas/grafico/', views.metricas_view, name='metricas'),
    # # # login 
    path('login/', login_view, name='login_view'),
    path('logout/', logout_view, name='logout'),
    # # # metricas
    path('dashboard_2/', dashboard_2, name='dashboard_2'),
    # # # correo
    path('enviar-correos/', enviar_correos_view, name='enviar_correos_view'),
    
    path('encuestas/', include('encuestas.urls')),  # Cambia 'nombre_de_la_app_encuestas' por el nombre real

]
