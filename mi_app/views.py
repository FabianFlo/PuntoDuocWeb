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

def format_fecha(fecha):
    if fecha:
        try:
            return datetime.fromisoformat(fecha).strftime('%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

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
            'descripcion': request.POST.get('descripcion'),
            'estado': request.POST.get('estado'),
            'fecha': format_fecha(request.POST.get('fecha')),
            'fecha_creacion': format_fecha(None),
            'imagen': request.POST.get('imagen'),
            'lugar': request.POST.get('lugar'),
            'sede': request.POST.get('sede'),
            'tipo': request.POST.get('tipo'),
            'titulo': request.POST.get('titulo'),
            'Cupos': request.POST.get('Cupos'),
        }

        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, headers=headers, json={"fields": {
            "id_evento": {"stringValue": id_evento},
            "descripcion": {"stringValue": datos['descripcion']},
            "estado": {"stringValue": datos['estado']},
            "fecha": {"timestampValue": datos['fecha']},
            "fecha_creacion": {"timestampValue": datos['fecha_creacion']},
            "imagen": {"stringValue": datos['imagen']},
            "lugar": {"stringValue": datos['lugar']},
            "sede": {"stringValue": datos['sede']},
            "tipo": {"stringValue": datos['tipo']},
            "titulo": {"stringValue": datos['titulo']},
            "Cupos": {"integerValue": datos['Cupos']},
            "inscritos": {"integerValue": "0"},
            "listaEspera": {"arrayValue": {"values": []}}
        }})

        if response.status_code in [200, 201]:
            messages.success(request, "Evento subido correctamente")
        else:
            messages.error(request, "Error al subir evento")

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
        datos = {
            'descripcion': request.POST.get('descripcion'),
            'estado': request.POST.get('estado'),
            'fecha': format_fecha(request.POST.get('fecha')),
            'imagen': request.POST.get('imagen'),
            'lugar': request.POST.get('lugar'),
            'sede': request.POST.get('sede'),
            'tipo': request.POST.get('tipo'),
            'titulo': request.POST.get('titulo'),
            'Cupos': request.POST.get('Cupos'),
        }

        headers = {"Content-Type": "application/json"}
        response = requests.patch(url, headers=headers, json={"fields": {
            "descripcion": {"stringValue": datos['descripcion']},
            "estado": {"stringValue": datos['estado']},
            "fecha": {"timestampValue": datos['fecha']},
            "imagen": {"stringValue": datos['imagen']},
            "lugar": {"stringValue": datos['lugar']},
            "sede": {"stringValue": datos['sede']},
            "tipo": {"stringValue": datos['tipo']},
            "titulo": {"stringValue": datos['titulo']},
            "Cupos": {"integerValue": datos['Cupos']},
            "inscritos": {"integerValue": "0"},
            "listaEspera": {"arrayValue": {"values": []}}
        }})

        if response.status_code in [200, 204]:
            messages.success(request, "Evento modificado correctamente")
            return render(request, 'mi_app/eventosCRUD/evento_modificar.html', {'evento': datos})
        else:
            messages.error(request, "Error al modificar el evento")

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

@login_required
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
    cantidad_encuestas_contestadas = len(set(respuesta['fields']['encuesta_id']['stringValue'] for respuesta in respuestas))

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

    inscritos_por_evento = {evento['fields']['titulo']['stringValue']: evento['fields'].get('inscritos', {}).get('integerValue', 0) for evento in eventos}
    carreras_con_mayor_participacion = Counter(estudiante['fields']['carrera']['stringValue'] for estudiante in estudiantes).most_common(5)
    promedio_eventos_por_estudiante = len(eventos) / len(estudiantes) if estudiantes else 0
    satisfaccion_participante = 0  # Asumiendo que no tienes estos datos aún

    # Gráficos
    grafico_inscritos = list(inscritos_por_evento.values())
    grafico_eventos = list(inscritos_por_evento.keys())

    # Preparar datos para gráfico de carreras
    labels_carreras = [carrera[0] for carrera in carreras_con_mayor_participacion]
    data_carreras = [carrera[1] for carrera in carreras_con_mayor_participacion]

    # Enviando datos al template
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
        'lista_espera_eventos': lista_espera_eventos,
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

@login_required
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
                'objetivo': mision['fields'].get('objetivo', {}).get('stringValue', 'Sin objetivo')
            }
            misiones_data.append(mision_data)

        # Pasar las misiones a la plantilla para que se muestren
        return render(request, 'mi_app/mision/listar_misiones.html', {'misiones': misiones_data})

    else:
        # Si hay un error al obtener las misiones
        return render(request, 'error.html', {'mensaje': 'Error al obtener las misiones.'})



def crear_mision(request):
    if request.method == 'POST':
        # Obtener el título, que se usará como el ID del documento
        titulo = request.POST.get('titulo')

        # Si no hay título, evitamos crear la misión
        if not titulo:
            return render(request, 'error.html', {'mensaje': 'El título es obligatorio.'})

        # Construir los datos que se enviarán a Firestore
        data = {
            "fields": {
                "titulo": {"stringValue": titulo},
                "descripcion": {"stringValue": request.POST.get('descripcion')},
                "puntaje": {"integerValue": int(request.POST.get('puntaje'))},
                "objetivo": {"stringValue": request.POST.get('objetivo')}
            }
        }
        
        # Usamos el título como el ID en la URL de Firestore
        url = f"{FIREBASE_URL}/{titulo}"  # Aquí añadimos el título a la URL para usarlo como ID
        
        # Hacer la solicitud POST a Firestore para crear el documento
        response = requests.patch(url, json=data)  # Usamos PATCH para actualizar o crear con un ID específico
        
        # Verificar si la misión fue creada correctamente
        if response.status_code == 200:
            return redirect('listar_misiones')  # Redirigir a la lista de misiones
        else:
            return render(request, 'error.html', {'mensaje': 'Error al crear la misión.'})

    return render(request, 'mi_app/mision/crear_mision.html')  # Renderizar el formulario para crear misión


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
                "objetivo": {"stringValue": request.POST.get('objetivo')}
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
    



