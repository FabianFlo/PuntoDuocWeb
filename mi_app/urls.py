from django.urls import include, path
from .views import *
from django.urls import path
from . import views


urlpatterns = [
    path('subir_evento/', subir_evento_view, name='subir_evento'),
    path('listar_eventos/', listar_eventos_view, name='listar_eventos'),
    path('eliminar_evento/<str:evento_id>/', eliminar_evento_view, name='eliminar_evento'),
    path('modificar_evento/<str:evento_id>/', modificar_evento_view, name='modificar_evento'),
    
    path('', home, name='home'),  # Ruta para el home page

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
    
    path('encuestas/', include('encuestas.urls')),

    path('misiones/', listar_misiones, name='listar_misiones'),
    path('misiones/crear/', crear_mision, name='crear_mision'),
    path('misiones/<str:mision_id>/', detalle_mision, name='detalle_mision'),
    path('misiones/<str:mision_id>/actualizar/', actualizar_mision, name='modificar_mision'),
    path('misiones/<str:mision_id>/eliminar/', eliminar_mision, name='eliminar_mision'),

    # # # gestor
    path('crear_gestor/',crear_gestor_view, name='crear_gestor' ),
    path('gestores/',listar_gestor_view, name='gestores' ),
    path('gestores_delete/<str:id_Geventos>/',eliminar_gestor_view, name='gestores_delete' ),
    path('gestores/modificar/<str:gestor_id>/', modificar_gestor_view, name='modificar_gestor'),

    path('boceto/',boceto, name='boceto' ),
    path('dashboard/',dashboard, name='dashboard' ),

    path('enviar_notificaciones/', enviar_notificaciones, name='enviar_notificaciones'),

    path('responder_consulta/<str:consulta_id>/', responder_consulta, name='responder_consulta'),
    path('panel-control/', panel_control, name='panel_control'),




]
