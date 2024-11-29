from collections import Counter
from django.contrib import messages
from django.shortcuts import render, redirect
import requests
from datetime import datetime
import uuid  # Importamos uuid para generar un identificador único
import io
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from django.http import HttpResponse
from django.core.mail import send_mail
import json
from pyfcm import FCMNotification
from django.conf import settings

# URL base de Firestore
FIRESTORE_BASE_URL = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents"

# mi_app/views.py
def enviar_notificaciones(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        cuerpo = request.POST.get('cuerpo')

        # Datos de la notificación
        notificacion = {
            "fields": {
                "titulo": {"stringValue": titulo},
                "cuerpo": {"stringValue": cuerpo},
                "leido": {"booleanValue": False},
                "timestamp": {"timestampValue": format_fecha(None)}
            }
        }

        # URL de Firestore para la colección "NotificacionesDirectas"
        url = f"{FIRESTORE_BASE_URL}/NotificacionesDirectas"

        # Enviar la notificación a Firestore
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(notificacion))

        if response.status_code == 200:
            messages.success(request, 'Notificación enviada con éxito')
        else:
            messages.error(request, 'Error al enviar la notificación')

        return redirect('enviar_notificaciones')

    return render(request, 'mi_app/enviar_notificaciones/enviar_notificaciones.html')

# mi_app/views.py
def metricas_page_view(request, event_id):
    print(f"Event ID: {event_id}")  # Añadir esta línea para verificar el ID del evento en la consola
    
    # URL de Firestore para obtener detalles del evento específico
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos/{event_id}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        evento = response.json()
        titulo = evento['fields']['titulo']['stringValue']
        Cupos = evento['fields']['Cupos']['integerValue']
        inscritos = evento['fields']['inscritos']['integerValue']
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 6))
        labels = ['Cupos', 'Inscritos']
        values = [Cupos, inscritos]
        ax.bar(labels, values, color=['blue', 'green'])
        ax.set_title(f'Evento: {titulo}')
        ax.set_ylabel('Cantidad')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        return HttpResponse(buffer, content_type='image/png')

    return HttpResponse(status=404)

def metricas_view(request):
    # URL de Firestore para la colección "Eventos"
    eventos_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    
    # URL de Firestore para la colección "Estudiantes"
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    
    # Obtener eventos
    eventos_response = requests.get(eventos_url)
    eventos = []
    if eventos_response.status_code == 200:
        eventos = eventos_response.json().get('documents', [])
        for evento in eventos:
            evento_id = evento['name'].split('/')[-1]  # Extraer solo el ID
            evento['id'] = evento_id  # Añadir el ID al evento
    
    # Obtener estudiantes
    estudiantes_response = requests.get(estudiantes_url)
    estudiantes = []
    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        for estudiante in estudiantes:
            estudiante_id = estudiante['name'].split('/')[-1]  # Extraer solo el ID del documento
            estudiante['id'] = estudiante_id  # Añadir el ID a los datos del estudiante
    
    # Pasar los datos de eventos y estudiantes al contexto
    context = {
        'eventos': eventos,
        'estudiantes': estudiantes,
    }

    return render(request, 'mi_app/metricas/metricas.html', context)

from datetime import datetime

def format_fecha(fecha_str):
    if not fecha_str:
        return datetime.utcnow().isoformat() + "Z"  # Fecha actual en formato UTC
    return datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M').isoformat() + "Z"

def login_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('usuario_autenticado'):
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('login_view')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# CRUD de Eventos
@login_required
def subir_evento_view(request):
    if request.method == 'POST':
        id_evento = str(uuid.uuid4())
        datos = {
            'descripcion': request.POST.get('descripcion', "Sin descripción"),
            'estado': request.POST.get('estado', "Pendiente"),
            'fecha': format_fecha(request.POST.get('fecha')),
            'fecha_termino': format_fecha(request.POST.get('fecha_termino')),
            'fecha_creacion': format_fecha(None),
            'imagen': request.POST.get('imagen', "https://via.placeholder.com/150"),
            'lugar': request.POST.get('lugar', "Lugar no especificado"),
            'sede': request.POST.get('sede', "Sin sede"),
            'categoria': request.POST.get('categoria', "General"),
            'carrera': request.POST.get('carrera', "Sin carrera"),
            'tipo_usuario': request.POST.get('tipo_usuario', "General"),
            'titulo': request.POST.get('titulo', "Evento sin título"),
            'Cupos': request.POST.get('cupos', "0"),  # Valor por defecto en caso de que el campo esté vacío

        }

        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, headers=headers, json={"fields": {
            "id_evento": {"stringValue": id_evento},
            "descripcion": {"stringValue": datos['descripcion']},
            "estado": {"stringValue": datos['estado']},
            "fecha": {"timestampValue": datos['fecha']},
            "fecha_termino": {"timestampValue": datos['fecha_termino']},
            "fecha_creacion": {"timestampValue": datos['fecha_creacion']},
            "imagen": {"stringValue": datos['imagen']},
            "lugar": {"stringValue": datos['lugar']},
            "sede": {"stringValue": datos['sede']},
            "categoria": {"stringValue": datos['categoria']},
            "carrera": {"stringValue": datos['carrera']},
            "tipo_usuario": {"stringValue": datos['tipo_usuario']},
            "titulo": {"stringValue": datos['titulo']},
            "Cupos": {"integerValue": int(datos['Cupos'])},  # Convierte el valor a entero
            "inscritos": {"integerValue": 0},
            "listaEspera": {"arrayValue": {"values": []}},
        }})

        if response.status_code in [200, 201]:
            messages.success(request, "Evento subido correctamente")
        else:
            print("Error al subir evento:", response.status_code, response.text)
            messages.error(request, f"Error al subir evento: {response.text}")

        return render(request, 'mi_app/eventosCRUD/subir_evento.html')

    return render(request, 'mi_app/eventosCRUD/subir_evento.html')


@login_required
def listar_eventos_view(request):
    url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    response = requests.get(url)
    eventos = []

    if response.status_code == 200:
        eventos = response.json().get('documents', [])
        for evento in eventos:
            evento_id = evento['name'].split('/')[-1]
            evento['id'] = evento_id

    return render(request, 'mi_app/eventosCRUD/listar_eventos.html', {'eventos': eventos})

@login_required
def eliminar_evento_view(request, evento_id):
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos/{evento_id}"
    if request.method == "POST":
        response = requests.delete(url)
        if response.status_code == 204:
            messages.success(request, "Evento eliminado correctamente")
        else:
            messages.error(request, "Error al eliminar el evento")
    return redirect('listar_eventos')

@login_required
def modificar_evento_view(request, evento_id):
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos/{evento_id}"

    if request.method == 'GET':
        response = requests.get(url)
        if response.status_code == 200:
            evento = response.json()['fields']
            return render(request, 'mi_app/eventosCRUD/evento_modificar.html', {'evento': evento})
        else:
            messages.error(request, "Error al obtener los datos del evento")
            return redirect('listar_eventos')

    elif request.method == 'POST':
        # Procesar los datos enviados desde el formulario
        datos = {
            'descripcion': request.POST.get('descripcion', "Sin descripción"),
            'estado': request.POST.get('estado', "Pendiente"),
            'fecha': format_fecha(request.POST.get('fecha')),
            'fecha_termino': format_fecha(request.POST.get('fecha_termino')),
            'imagen': request.POST.get('imagen', "https://via.placeholder.com/150"),
            'lugar': request.POST.get('lugar', "Lugar no especificado"),
            'sede': request.POST.get('sede', "Sin sede"),
            'tipo': request.POST.get('tipo', "General"),  # Manejo de valores vacíos
            'titulo': request.POST.get('titulo', "Evento sin título"),
            'Cupos': int(request.POST.get('Cupos', 0)),  # Convertir a entero
        }

        # Depuración
        print("Datos enviados desde el formulario:", datos)

        headers = {"Content-Type": "application/json"}
        response = requests.patch(url, headers=headers, json={"fields": {
            "descripcion": {"stringValue": datos['descripcion']},
            "estado": {"stringValue": datos['estado']},
            "fecha": {"timestampValue": datos['fecha']},
            "fecha_termino": {"timestampValue": datos['fecha_termino']},
            "imagen": {"stringValue": datos['imagen']},
            "lugar": {"stringValue": datos['lugar']},
            "sede": {"stringValue": datos['sede']},
            "tipo": {"stringValue": datos['tipo']},  # Campo corregido
            "titulo": {"stringValue": datos['titulo']},
            "Cupos": {"integerValue": datos['Cupos']},  # Convertir a entero
            "inscritos": {"integerValue": 0},  # Mantener valor inicial
            "listaEspera": {"arrayValue": {"values": []}},
        }})

        if response.status_code in [200, 204]:
            messages.success(request, "Evento modificado correctamente")
            return redirect('listar_eventos')
        else:
            print("Error al modificar el evento:", response.status_code, response.text)
            messages.error(request, f"Error al modificar el evento: {response.text}")

    return redirect('listar_eventos')





# Home
def home_view(request):
    return render(request, 'mi_app/home.html')

# CRUD Estudiantes
@login_required
def crear_estudiante_view(request):
    if request.method == 'POST':
        id_estudiante = str(uuid.uuid4())
        datos = {
            'nombre_completo': request.POST.get('nombre_completo'),
            'rut': request.POST.get('rut'),
            'telefono': request.POST.get('telefono'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'carrera': request.POST.get('carrera'),
        }

        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json={"fields": {
            "id_estudiante": {"stringValue": id_estudiante},
            "Nombre_completo": {"stringValue": datos['nombre_completo']},
            "Rut": {"stringValue": datos['rut']},
            "Telefono": {"stringValue": datos['telefono']},
            "email": {"stringValue": datos['email']},
            "password": {"stringValue": datos['password']},
            "carrera": {"stringValue": datos['carrera']},
            "puntaje": {"integerValue": "0"},
            "codigoQr": {"stringValue": ""},
            "eventosInscritos": {"arrayValue": {"values": []}}
        }})

        if response.status_code in [200, 201]:
            messages.success(request, "Estudiante creado correctamente.")
        else:
            messages.error(request, "Error al crear el estudiante.")

        return render(request, 'mi_app/estudiantesCRUD/crear_estudiante.html')

    return render(request, 'mi_app/estudiantesCRUD/crear_estudiante.html')

@login_required
def listar_estudiantes_view(request):
    url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    response = requests.get(url)
    estudiantes = []

    if response.status_code == 200:
        estudiantes = response.json().get('documents', [])
        for estudiante in estudiantes:
            estudiante_id = estudiante['name'].split('/')[-1]
            estudiante['id'] = estudiante_id

    return render(request, 'mi_app/estudiantesCRUD/listar_estudiantes.html', {'estudiantes': estudiantes})

@login_required
def eliminar_estudiante_view(request, estudiante_id):
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes/{estudiante_id}"
    if request.method == "POST":
        response = requests.delete(url)
        if response.status_code == 204:
            messages.success(request, "Estudiante eliminado correctamente.")
        else:
            messages.error(request, "Error al eliminar el estudiante.")
    return redirect('listar_estudiantes')

@login_required
def modificar_estudiante_view(request, estudiante_id):
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes/{estudiante_id}"

    if request.method == "POST":
        datos = {
            'Nombre_completo': request.POST.get('nombre_completo'),
            'Rut': request.POST.get('rut'),
            'Telefono': request.POST.get('telefono'),
            'email': request.POST.get('email'),
            'id_estudiante': estudiante_id,
            'password': request.POST.get('password'),
            'carrera': request.POST.get('carrera'),
            'puntaje': request.POST.get('puntaje', 0)
        }

        fields = {k: {"stringValue": v} for k, v in datos.items() if isinstance(v, str)}
        fields['puntaje'] = {"integerValue": int(datos['puntaje'])}

        response = requests.patch(url, json={"fields": fields})

        if response.status_code in [200, 204]:
            messages.success(request, "Estudiante modificado correctamente.")
            return redirect('listar_estudiantes')

    response = requests.get(url)
    if response.status_code == 200:
        estudiante = response.json().get('fields', {})
        return render(request, 'mi_app/estudiantesCRUD/modificar_estudiante.html', {'estudiante': estudiante})

    return redirect('listar_estudiantes')
# login 
def login_view(request):
    if request.method == 'POST':
        correo_electronico = request.POST.get('Correo_electronico')
        contrasena = request.POST.get('Contraseña')

        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Administrador"
        response = requests.get(url)

        if response.status_code == 200:
            administradores = response.json().get('documents', [])
            for admin in administradores:
                admin_data = admin['fields']
                email = admin_data.get('Correo_electronico', {}).get('stringValue')
                password = admin_data.get('Contraseña', {}).get('stringValue')

                if email == correo_electronico and password == contrasena:
                    request.session['usuario_autenticado'] = True
                    messages.success(request, 'Login exitoso!')
                    return redirect('home')  # Redirige a la página de inicio

        messages.error(request, 'Credenciales inválidas')

    return render(request, 'mi_app/authenticate/login.html', {
        'usuario_autenticado': request.session.get('usuario_autenticado', False)
    })
    
def logout_view(request):
    request.session.flush()  # Elimina todos los datos de la sesión
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('login_view')

from django.shortcuts import render
import requests
import json
from collections import Counter
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required

def dashboard_2(request):
    # URLs de las colecciones en Firebase
    eventos_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    respuestas_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Respuestas"

    # Obtener datos de Firebase
    eventos_response = requests.get(eventos_url)
    estudiantes_response = requests.get(estudiantes_url)
    respuestas_response = requests.get(respuestas_url)

    eventos = []
    estudiantes = []
    respuestas = []

    if eventos_response.status_code == 200:
        eventos = eventos_response.json().get('documents', [])
        for evento in eventos:
            evento_id = evento['name'].split('/')[-1]
            evento['id'] = evento_id

    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        for estudiante in estudiantes:
            estudiante_id = estudiante['name'].split('/')[-1]
            estudiante['id'] = estudiante_id

    if respuestas_response.status_code == 200:
        respuestas = respuestas_response.json().get('documents', [])

    # KPIs
    # Cantidad de Encuestas Contestadas
    cantidad_encuestas_contestadas = len(set(respuesta['fields'].get('encuesta_id', {}).get('stringValue', '') for respuesta in respuestas))

    # Diferentes id_estudiante en "Estudiantes" y "Inscripciones" dentro de "Eventos"
    id_estudiantes_totales = set(estudiante['id'] for estudiante in estudiantes)
    id_estudiantes_inscripciones = set(
        inscripcion['mapValue']['fields'].get('id_estudiante', {}).get('stringValue', '')
        for evento in eventos
        for inscripcion in evento['fields'].get('Inscripciones', {}).get('arrayValue', {}).get('values', [])
        if 'id_estudiante' in inscripcion['mapValue']['fields']
    )

    diferentes_estudiantes_totales = len(id_estudiantes_totales)
    diferentes_estudiantes_inscripciones = len(id_estudiantes_inscripciones)

    # Datos para gráfico de torta
    data_estudiantes = {
        'Totales': diferentes_estudiantes_totales,
        'Inscripciones': diferentes_estudiantes_inscripciones,
    }

    # Número de "id_estudiante" en "listaEspera" para cada evento
    lista_espera_eventos = sorted(
        [
            (
                evento['fields']['titulo']['stringValue'],
                len(evento['fields'].get('listaEspera', {}).get('arrayValue', {}).get('values', [])),
                int(evento['fields'].get('Cupos', {}).get('integerValue', 0)) - int(evento['fields'].get('inscritos', {}).get('integerValue', 0))
            )
            for evento in eventos
        ],
        key=lambda x: x[1],
        reverse=True
    )

    # Número de inscritos por evento
    inscritos_por_evento = {
        evento['fields']['titulo']['stringValue']: evento['fields'].get('inscritos', {}).get('integerValue', 0)
        for evento in eventos
    }

    # Carreras con mayor participación
    carreras_con_mayor_participacion = Counter(
        estudiante['fields'].get('carrera', {}).get('stringValue', 'Desconocido')
        for estudiante in estudiantes
    ).most_common(5)

    # Promedio de eventos por estudiante
    promedio_eventos_por_estudiante = len(eventos) / len(estudiantes) if estudiantes else 0

    satisfaccion_participante = 0  # Asumimos que no tienes estos datos aún

    # Gráficos
    grafico_inscritos = list(inscritos_por_evento.values())
    grafico_eventos = list(inscritos_por_evento.keys())

    # Preparar datos para gráfico de carreras
    labels_carreras = [carrera[0] for carrera in carreras_con_mayor_participacion]
    data_carreras = [carrera[1] for carrera in carreras_con_mayor_participacion]

    context = {
        'eventos': eventos,
        'estudiantes': estudiantes,
        'inscritos_por_evento': inscritos_por_evento,
        'carreras_con_mayor_participacion': carreras_con_mayor_participacion,
        'promedio_eventos_por_estudiante': promedio_eventos_por_estudiante,
        'satisfaccion_participante': satisfaccion_participante,
        'grafico_inscritos': grafico_inscritos,
        'grafico_eventos': grafico_eventos,
        'labels_carreras': labels_carreras,
        'data_carreras': data_carreras,
        'cantidad_encuestas_contestadas': cantidad_encuestas_contestadas,
        'data_estudiantes': json.dumps(data_estudiantes),
    }

    return render(request, 'mi_app/dashboard/dashboard_2.html', context)


def obtener_correos_por_carrera(carrera):
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    estudiantes_response = requests.get(estudiantes_url)

    correos = []
    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        for estudiante in estudiantes:
            fields = estudiante['fields']
            if fields.get('carrera', {}).get('stringValue') == carrera:
                correos.append(fields.get('email', {}).get('stringValue'))

    return correos

def obtener_correos_por_carrera(carrera):
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    estudiantes_response = requests.get(estudiantes_url)

    correos = []
    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        for estudiante in estudiantes:
            fields = estudiante['fields']
            if fields.get('carrera', {}).get('stringValue') == carrera:
                correos.append(fields.get('email', {}).get('stringValue'))

    return correos

def obtener_carreras():
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    estudiantes_response = requests.get(estudiantes_url)

    carreras = set()
    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        for estudiante in estudiantes:
            carrera = estudiante['fields'].get('carrera', {}).get('stringValue')
            if carrera:
                carreras.add(carrera)

    return list(carreras)

def obtener_correos_por_evento(titulo_evento):
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    eventos_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"

    estudiantes_response = requests.get(estudiantes_url)
    correos = []

    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        for estudiante in estudiantes:
            fields = estudiante['fields']
            if fields.get('eventosInscritos', {}).get('arrayValue', {}).get('values', []):
                for evento in fields['eventosInscritos']['arrayValue']['values']:
                    if evento.get('stringValue') == titulo_evento:
                        correos.append(fields.get('email', {}).get('stringValue'))

    return correos

def enviar_correos_view(request):
    if request.method == 'POST':
        # Obtener el asunto y mensaje
        asunto = request.POST.get('asunto_evento') or request.POST.get('asunto_carrera')
        mensaje = request.POST.get('mensaje_evento') or request.POST.get('mensaje_carrera')

        # Obtener el ID de la encuesta
        encuesta_id = request.POST.get('encuesta_id')  # Asegúrate de que este ID se envíe en el formulario
        enlace_encuesta = f"http://127.0.0.1:8000/encuestas/responder/{encuesta_id}"  # Modifica según tu dominio y ruta

        # Añadir el enlace de la encuesta al mensaje
        mensaje += f"\n\nPuedes acceder a la encuesta aquí: {enlace_encuesta}"

        # Enviar correos por evento
        if request.POST.get('tipo') == 'evento':
            titulo_evento = request.POST['titulo_evento']
            correos_destinatarios = obtener_correos_por_evento(titulo_evento)

            if not correos_destinatarios:
                messages.error(request, "No se encontraron correos para el evento seleccionado.")
            else:
                for email in correos_destinatarios:
                    try:
                        send_mail(asunto, mensaje, 'punto.estudiantil.puntoduoc@gmail.com', [email])
                    except Exception as e:
                        messages.error(request, f"Error al enviar correo a {email}: {str(e)}")

                messages.success(request, "Correos enviados exitosamente por evento.")

        # Enviar correos por carrera
        elif request.POST.get('tipo') == 'carrera':
            carrera = request.POST['carrera']
            correos_destinatarios = obtener_correos_por_carrera(carrera)

            if not correos_destinatarios:
                messages.error(request, "No se encontraron correos para la carrera seleccionada.")
            else:
                for email in correos_destinatarios:
                    try:
                        send_mail(asunto, mensaje, 'punto.estudiantil.puntoduoc@gmail.com', [email])
                    except Exception as e:
                        messages.error(request, f"Error al enviar correo a {email}: {str(e)}")

                messages.success(request, "Correos enviados exitosamente por carrera.")

        return redirect('enviar_correos_view')

    # Obtener títulos de eventos
    eventos_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    eventos_response = requests.get(eventos_url)

    titulos_eventos = []
    if eventos_response.status_code == 200:
        eventos = eventos_response.json().get('documents', [])
        for evento in eventos:
            titulos_eventos.append(evento['fields']['titulo']['stringValue'])

    # Obtener carreras
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    estudiantes_response = requests.get(estudiantes_url)

    carreras = []
    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        carreras = list(set(estudiante['fields']['carrera']['stringValue'] for estudiante in estudiantes))

    # Obtener encuestas
    encuestas_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Encuestas"
    encuestas_response = requests.get(encuestas_url)

    encuestas = []
    if encuestas_response.status_code == 200:
        encuestas = encuestas_response.json().get('documents', [])

    # Preparar la lista de encuestas con ID y nombre
    encuestas_list = [
    {
        'id': encuesta['name'].split('/')[-1],  # Extrae el ID del documento
        'nombre': encuesta['fields']['nombre']['stringValue']
    }
    for encuesta in encuestas if 'nombre' in encuesta['fields']
]
    for encuesta in encuestas:
        encuesta_id = encuesta.get('fields', {}).get('id', {}).get('stringValue', None)
        encuesta_nombre = encuesta.get('fields', {}).get('nombre', {}).get('stringValue', None)

        if encuesta_id and encuesta_nombre:  # Asegúrate de que ambos valores estén presentes
            encuestas_list.append({'id': encuesta_id, 'nombre': encuesta_nombre})

    return render(request, 'mi_app/difucion/enviar_correos.html', {
        'titulos_eventos': titulos_eventos, 
        'carreras': carreras,
        'encuestas': encuestas_list
    })
import requests
from django.shortcuts import render, redirect

# URL base para interactuar con Firestore
FIREBASE_URL = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Misiones"

def listar_misiones(request):
    # Realizar la solicitud GET a Firestore
    response = requests.get(FIREBASE_URL)

    if response.status_code == 200:
        # Obtener las misiones de la respuesta
        misiones = response.json().get('documents', [])

        # Lista para almacenar las misiones procesadas
        misiones_data = []

        # Recorrer cada misión y extraer los datos necesarios
        for mision in misiones:
            mision_id = mision['name'].split('/')[-1]  # Obtener el ID de la misión (es el título)

            mision_data = {
                'id': mision_id,  # El ID es el título de la misión
                'titulo': mision_id,  # Usamos el título como ID de la misión
                'descripcion': mision['fields'].get('descripcion', {}).get('stringValue', 'Sin descripción'),
                'puntaje': mision['fields'].get('puntaje', {}).get('integerValue', 0),
                'objetivo': mision['fields'].get('objetivo', {}).get('stringValue', 'Sin objetivo'),
                'categoria': mision['fields'].get('categoria', {}).get('stringValue', 'Sin categoría'),
                'meta': mision['fields'].get('meta', {}).get('integerValue', 0)
            }
            misiones_data.append(mision_data)

        # Pasar las misiones a la plantilla para que se muestren
        return render(request, 'mi_app/mision/listar_misiones.html', {'misiones': misiones_data})

    else:
        # Si hay un error al obtener las misiones
        return render(request, 'error.html', {'mensaje': 'Error al obtener las misiones.'})


def crear_mision(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        if not titulo:
            return render(request, 'error.html', {'mensaje': 'El título es obligatorio.'})

        data = {
            "fields": {
                "titulo": {"stringValue": titulo},
                "descripcion": {"stringValue": request.POST.get('descripcion')},
                "puntaje": {"integerValue": int(request.POST.get('puntaje'))},
                "objetivo": {"stringValue": request.POST.get('objetivo')},
                "categoria": {"stringValue": request.POST.get('categoria')},
                "meta": {"integerValue": int(request.POST.get('meta'))}
            }
        }
        url = f"{FIREBASE_URL}/{titulo}"
        response = requests.patch(url, json=data)
        if response.status_code == 200:
            return redirect('listar_misiones')
        else:
            return render(request, 'error.html', {'mensaje': 'Error al crear la misión.'})

    return render(request, 'mi_app/mision/crear_mision.html')
# Detalle de misión
def detalle_mision(request, mision_id):
    response = requests.get(f"{FIREBASE_URL}/{mision_id}")
    if response.status_code == 200:
        mision = response.json()['fields']
        mision_data = {
            'id': mision_id,
            'titulo': mision['titulo']['stringValue'],
            'descripcion': mision['descripcion']['stringValue'],
            'puntaje': mision['puntaje']['integerValue'],
            'parametros': [p['stringValue'] for p in mision['parametros']['arrayValue']['values']],
        }
        return render(request, 'mi_app/mision/detalle_mision.html', {'mision': mision_data})
    else:
        return render(request, 'error.html', {'mensaje': 'La misión no existe.'})

def actualizar_mision(request, mision_id):
    if request.method == 'POST':
        data = {
            "fields": {
                "titulo": {"stringValue": request.POST.get('titulo')},
                "descripcion": {"stringValue": request.POST.get('descripcion')},
                "puntaje": {"integerValue": int(request.POST.get('puntaje'))},
                "objetivo": {"stringValue": request.POST.get('objetivo')},
                "categoria": {"stringValue": request.POST.get('categoria')},
                "meta": {"integerValue": int(request.POST.get('meta'))}
            }
        }
        response = requests.patch(f"{FIREBASE_URL}/{mision_id}", json=data)
        if response.status_code == 200:
            return redirect('listar_misiones')
        else:
            return render(request, 'error.html', {'mensaje': 'Error al actualizar la misión.'})

    response = requests.get(f"{FIREBASE_URL}/{mision_id}")
    if response.status_code == 200:
        mision = response.json()['fields']
        mision_data = {
            'id': mision_id,
            'titulo': mision['titulo']['stringValue'],
            'descripcion': mision['descripcion']['stringValue'],
            'puntaje': mision['puntaje']['integerValue'],
            'objetivo': mision['objetivo']['stringValue'],
            'categoria': mision['categoria']['stringValue'],
            'meta': mision['meta']['integerValue']
        }
        return render(request, 'mi_app/mision/actualizar_mision.html', {'mision': mision_data})
    else:
        return render(request, 'error.html', {'mensaje': 'La misión no existe.'})


def detalle_mision(request, mision_id):
    response = requests.get(f"{FIREBASE_URL}/{mision_id}")
    if response.status_code == 200:
        mision = response.json()['fields']
        mision_data = {
            'id': mision_id,
            'titulo': mision['titulo']['stringValue'],
            'descripcion': mision['descripcion']['stringValue'],
            'puntaje': mision['puntaje']['integerValue'],
            'objetivo': mision['objetivo']['stringValue'],
        }
        return render(request, 'mi_app/mision/detalle_mision.html', {'mision': mision_data})
    else:
        return render(request, 'error.html', {'mensaje': 'La misión no existe.'})

# Eliminar misión
def eliminar_mision(request, mision_id):
    if request.method == 'POST':
        response = requests.delete(f"{FIREBASE_URL}/{mision_id}")
        if response.status_code == 200:
            return redirect('listar_misiones')
        else:
            return render(request, 'error.html', {'mensaje': 'Error al eliminar la misión.'})

    response = requests.get(f"{FIREBASE_URL}/{mision_id}")
    if response.status_code == 200:
        mision = response.json()['fields']
        mision_data = {
            'id': mision_id,
            'titulo': mision['titulo']['stringValue'],
            'descripcion': mision['descripcion']['stringValue'],
            'puntaje': mision['puntaje']['integerValue'],
            'objetivo': mision['objetivo']['stringValue'],
        }
        return redirect('listar_misiones', {'mision': mision_data})
    else:
        return render(request, 'error.html', {'mensaje': 'La misión no existe.'})

def crear_gestor_view(request):
    if request.method == 'POST':
        id_Geventos = str(uuid.uuid4())
        datos = {
            'nombre_completo': request.POST.get('nombre_completo'),
            'rut': request.POST.get('rut'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
        }

        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json={"fields": {
            "id_Geventos": {"stringValue": id_Geventos},
            "Nombre_completo": {"stringValue": datos['nombre_completo']},
            "rut": {"stringValue": datos['rut']},
            "email": {"stringValue": datos['email']},
            "password": {"stringValue": datos['password']},
        }})

        if response.status_code in [200, 201]:
            messages.success(request, "Gestor de eventos creado creado correctamente.")
        else:
            messages.error(request, "Error al crear el Gestor.")

        return render(request, 'mi_app/gestorCRUD/crear_gestor.html')

    return render(request, 'mi_app/gestorCRUD/crear_gestor.html')

def listar_gestor_view(request):
    url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos"
    response = requests.get(url)
    gestores = []

    if response.status_code == 200:
        gestores = response.json().get('documents', [])
        for gestor in gestores:
            id_Geventos = gestor['name'].split('/')[-1]
            gestor['id'] = id_Geventos

    return render(request, 'mi_app/gestorCRUD/listar_gestor.html', {'gestores': gestores})

def eliminar_gestor_view(request, id_Geventos):
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos/{id_Geventos}"
    if request.method == "POST":
        response = requests.delete(url)
        if response.status_code == 204:
            messages.success(request, "Gestor eliminado correctamente.")
        else:
            messages.error(request, "Error al eliminar el Gestor.")
    return redirect('gestores')

def modificar_gestor_view(request, gestor_id):
    # URL del gestor en Firestore
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos/{gestor_id}"
    headers = {"Content-Type": "application/json"}

    # Obtener los datos actuales del gestor
    response = requests.get(url, headers=headers)

    # Si no se encuentra el gestor, redirigir con un mensaje de error
    if response.status_code != 200:
        messages.error(request, "No se pudo encontrar el Gestor.")
        return redirect('gestores')

    # Obtener los datos actuales del gestor
    gestor_data = response.json()['fields']
    nombre_completo = gestor_data['Nombre_completo']['stringValue']
    rut = gestor_data['rut']['stringValue']
    email = gestor_data['email']['stringValue']
    password = gestor_data['password']['stringValue']

    if request.method == 'POST':
        # Obtener los nuevos datos del formulario
        nuevo_nombre_completo = request.POST.get('nombre_completo')
        nuevo_rut = request.POST.get('rut')
        nuevo_email = request.POST.get('email')
        nuevo_password = request.POST.get('password')

        # Validación básica de los campos
        if not nuevo_nombre_completo or not nuevo_rut or not nuevo_email or not nuevo_password:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'mi_app/gestorCRUD/modificar_gestor.html', {
                'gestor_id': gestor_id,
                'nombre_completo': nombre_completo,
                'rut': rut,
                'email': email,
                'password': password
            })

        # Payload para actualizar el gestor
        payload = {
            "fields": {
                "Nombre_completo": {"stringValue": nuevo_nombre_completo},
                "rut": {"stringValue": nuevo_rut},
                "email": {"stringValue": nuevo_email},
                "password": {"stringValue": nuevo_password},
            }
        }

        # Enviar solicitud PATCH para actualizar los datos
        response = requests.patch(url, headers=headers, json=payload)

        # Verificar si la actualización fue exitosa
        if response.status_code == 200:
            messages.success(request, "Gestor de eventos modificado correctamente.")
            return redirect('gestores')  # Redirigir al listado de gestores
        else:
            messages.error(request, "Error al modificar el Gestor.")

    # Si la solicitud no es POST, simplemente renderizamos el formulario con los datos actuales
    return render(request, 'mi_app/gestorCRUD/modificar_gestor.html', {
        'gestor_id': gestor_id,
        'nombre_completo': nombre_completo,
        'rut': rut,
        'email': email,
        'password': password
    })

def boceto(request):
    return render(request,'mi_app/boceto.html')

import requests
from django.shortcuts import render

def dashboard(request):
    # Obtener eventos desde Firestore
    url_eventos = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    response_eventos = requests.get(url_eventos)
    eventos = []

    if response_eventos.status_code == 200:
        eventos = response_eventos.json().get('documents', [])
        for evento in eventos:
            evento_id = evento['name'].split('/')[-1]
            evento['id'] = evento_id

    # Obtener gestores desde Firestore
    url_gestores = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos"
    response_gestores = requests.get(url_gestores)
    gestores = []

    if response_gestores.status_code == 200:
        gestores = response_gestores.json().get('documents', [])
        for gestor in gestores:
            gestor_id = gestor['name'].split('/')[-1]
            gestor['id'] = gestor_id
            gestor['email'] = gestor['fields']['email']['stringValue']  # Tomamos el correo del gestor

    # Procesar el formulario de asignación de gestores
    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')  # Obtener el ID del evento
        gestor_id = request.POST.get('gestor_id')  # Obtener el ID del gestor seleccionado

        # Buscar el gestor seleccionado por ID
        gestor_seleccionado = next((g for g in gestores if g['id'] == gestor_id), None)

        if gestor_seleccionado:
            # Buscar el evento correspondiente al evento_id
            evento_seleccionado = next((e for e in eventos if e['id'] == evento_id), None)

            if evento_seleccionado:
                try:
                    # Extraer los datos relevantes para el correo
                    titulo_evento = evento_seleccionado['fields']['titulo']['stringValue']
                    fecha_evento = evento_seleccionado['fields']['fecha']['timestampValue']  # Asegúrate de que este valor sea accesible
                    nombre_gestor = gestor_seleccionado['fields']['Nombre_completo']['stringValue']

                    # Enviar el correo
                    subject = f'Nuevo Evento Asignado: {titulo_evento}'
                    message = f'Hola {nombre_gestor},\n\nSe te ha asignado el evento "{titulo_evento}" para su gestión. El evento será realizado el {fecha_evento}.'
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[gestor_seleccionado['email']]
                    )

                except Exception as e:
                    print(f"Error al enviar el correo: {str(e)}")
                    return render(request, 'mi_app/dashboard/dashboard.html', {'eventos': eventos, 'gestores': gestores, 'error': 'Hubo un problema al enviar el correo.'})

        # Redirigir al dashboard si todo fue exitoso
        return redirect('dashboard')

    # Pasar los eventos y los gestores a la plantilla
    return render(request, 'mi_app/dashboard/dashboard.html', {'eventos': eventos, 'gestores': gestores})
