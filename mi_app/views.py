from collections import Counter
from django.contrib import messages
from django.shortcuts import render, redirect
import requests
from datetime import datetime
import uuid 
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from django.http import HttpResponse
from django.core.mail import send_mail
import json
from pyfcm import FCMNotification
from django.conf import settings
from django.contrib.auth.decorators import login_required

FIRESTORE_BASE_URL = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents"

def enviar_notificaciones(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        cuerpo = request.POST.get('cuerpo')
        destinatario = request.POST.get('destinatario')

        url = f"{FIRESTORE_BASE_URL}/NotificacionesDirectas"

        destinatario = request.POST.get('destinatario')  

        usuarios = []
        if destinatario == 'todos':
            estudiantes_url = f"{FIRESTORE_BASE_URL}/Estudiantes"
            invitados_url = f"{FIRESTORE_BASE_URL}/Invitados"
            estudiantes_response = requests.get(estudiantes_url)
            invitados_response = requests.get(invitados_url)
            if estudiantes_response.status_code == 200:
                estudiantes_data = estudiantes_response.json().get('documents', [])
                usuarios.extend(estudiantes_data)
            if invitados_response.status_code == 200:
                invitados_data = invitados_response.json().get('documents', [])
                usuarios.extend(invitados_data)
        elif destinatario == 'estudiante':
            estudiantes_url = f"{FIRESTORE_BASE_URL}/Estudiantes"
            estudiantes_response = requests.get(estudiantes_url)
            if estudiantes_response.status_code == 200:
                estudiantes_data = estudiantes_response.json().get('documents', [])
                usuarios.extend(estudiantes_data)
        elif destinatario == 'invitado':
            invitados_url = f"{FIRESTORE_BASE_URL}/Invitados"
            invitados_response = requests.get(invitados_url)
            if invitados_response.status_code == 200:
                invitados_data = invitados_response.json().get('documents', [])
                usuarios.extend(invitados_data)

        usuario_ids = [{
            "mapValue": {
                "fields": {
                    "userId": {"stringValue": user['name'].split('/')[-1]},
                    "leido": {"booleanValue": False}
                }
            }
        } for user in usuarios]

        notificacion = {
            "fields": {
                "titulo": {"stringValue": titulo},
                "cuerpo": {"stringValue": cuerpo},
                "leido": {"booleanValue": False},
                "timestamp": {"timestampValue": format_fecha(None)},
                "usuarioIds": {"arrayValue": {"values": usuario_ids}},
                "destinatario": {"stringValue": destinatario}
            }
        }

        response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(notificacion))

        if response.status_code == 200:
            messages.success(request, 'Notificación enviada con éxito')
        else:
            messages.error(request, 'Error al enviar la notificación')
        return redirect('enviar_notificaciones')

    return render(request, 'mi_app/enviar_notificaciones/enviar_notificaciones.html')

def metricas_page_view(request, event_id):
    print(f"Event ID: {event_id}")  
    
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
    eventos_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    
    eventos_response = requests.get(eventos_url)
    eventos = []
    if eventos_response.status_code == 200:
        eventos = eventos_response.json().get('documents', [])
        for evento in eventos:
            evento_id = evento['name'].split('/')[-1]  
            evento['id'] = evento_id 
    
    estudiantes_response = requests.get(estudiantes_url)
    estudiantes = []
    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        for estudiante in estudiantes:
            estudiante_id = estudiante['name'].split('/')[-1] 
            estudiante['id'] = estudiante_id  
    
    context = {
        'eventos': eventos,
        'estudiantes': estudiantes,
    }

    return render(request, 'mi_app/metricas/metricas.html', context)

from datetime import datetime

def format_fecha(fecha_str):
    if not fecha_str:
        return datetime.utcnow().isoformat() + "Z"
    return datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M').isoformat() + "Z"

def login_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('usuario_autenticado'):
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect('login_view')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

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
            'Cupos': request.POST.get('cupos', "0"),
            'gestor': "Sin gestor",

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
            "Cupos": {"integerValue": int(datos['Cupos'])},
            "inscritos": {"integerValue": 0},
            "listaEspera": {"arrayValue": {"values": []}},
            "gestor": {"stringValue": datos['gestor']},
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
        datos = {
            'descripcion': request.POST.get('descripcion', "Sin descripción"),
            'estado': request.POST.get('estado', "Pendiente"),
            'fecha': format_fecha(request.POST.get('fecha')),
            'fecha_termino': format_fecha(request.POST.get('fecha_termino')),
            'imagen': request.POST.get('imagen', "https://via.placeholder.com/150"),
            'lugar': request.POST.get('lugar', "Lugar no especificado"),
            'sede': request.POST.get('sede', "Sin sede"),
            'tipo': request.POST.get('tipo', "General"),
            'titulo': request.POST.get('titulo', "Evento sin título"),
            'Cupos': int(request.POST.get('Cupos', 0)),
        }

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
            "tipo": {"stringValue": datos['tipo']},
            "titulo": {"stringValue": datos['titulo']},
            "Cupos": {"integerValue": datos['Cupos']},
            "inscritos": {"integerValue": 0},
            "listaEspera": {"arrayValue": {"values": []}},
        }})

        if response.status_code in [200, 204]:
            messages.success(request, "Evento modificado correctamente")
            return redirect('listar_eventos')
        else:
            print("Error al modificar el evento:", response.status_code, response.text)
            messages.error(request, f"Error al modificar el evento: {response.text}")

    return redirect('listar_eventos')

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
                    return redirect('home')

        messages.error(request, 'Credenciales inválidas')

    return render(request, 'mi_app/authenticate/login.html', {
        'usuario_autenticado': request.session.get('usuario_autenticado', False)
    })
    
def logout_view(request):
    request.session.flush()
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('login_view')

def dashboard_2(request):
    eventos_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    respuestas_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Respuestas"

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

    cantidad_encuestas_contestadas = len(set(respuesta['fields'].get('encuesta_id', {}).get('stringValue', '') for respuesta in respuestas))

    id_estudiantes_totales = set(estudiante['id'] for estudiante in estudiantes)
    id_estudiantes_inscripciones = set(
        inscripcion['mapValue']['fields'].get('id_estudiante', {}).get('stringValue', '')
        for evento in eventos
        for inscripcion in evento['fields'].get('Inscripciones', {}).get('arrayValue', {}).get('values', [])
        if 'id_estudiante' in inscripcion['mapValue']['fields']
    )

    diferentes_estudiantes_totales = len(id_estudiantes_totales)
    diferentes_estudiantes_inscripciones = len(id_estudiantes_inscripciones)

    data_estudiantes = {
        'Totales': diferentes_estudiantes_totales,
        'Inscripciones': diferentes_estudiantes_inscripciones,
    }

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

    inscritos_por_evento = {
        evento['fields']['titulo']['stringValue']: evento['fields'].get('inscritos', {}).get('integerValue', 0)
        for evento in eventos
    }

    carreras_con_mayor_participacion = Counter(
        estudiante['fields'].get('carrera', {}).get('stringValue', 'Desconocido')
        for estudiante in estudiantes
    ).most_common(5)

    promedio_eventos_por_estudiante = len(eventos) / len(estudiantes) if estudiantes else 0

    satisfaccion_participante = 0

    grafico_inscritos = list(inscritos_por_evento.values())
    grafico_eventos = list(inscritos_por_evento.keys())

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
        asunto = request.POST.get('asunto_evento') or request.POST.get('asunto_carrera')
        mensaje = request.POST.get('mensaje_evento') or request.POST.get('mensaje_carrera')

        encuesta_id = request.POST.get('encuesta_id')
        enlace_encuesta = f"http://127.0.0.1:8000/encuestas/responder/{encuesta_id}"

        mensaje += f"\n\nPuedes acceder a la encuesta aquí: {enlace_encuesta}"

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

    eventos_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    eventos_response = requests.get(eventos_url)

    titulos_eventos = []
    if eventos_response.status_code == 200:
        eventos = eventos_response.json().get('documents', [])
        for evento in eventos:
            titulos_eventos.append(evento['fields']['titulo']['stringValue'])

    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    estudiantes_response = requests.get(estudiantes_url)

    carreras = []
    if estudiantes_response.status_code == 200:
        estudiantes = estudiantes_response.json().get('documents', [])
        carreras = list(set(estudiante['fields']['carrera']['stringValue'] for estudiante in estudiantes))

    encuestas_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Encuestas"
    encuestas_response = requests.get(encuestas_url)

    encuestas = []
    if encuestas_response.status_code == 200:
        encuestas = encuestas_response.json().get('documents', [])

    encuestas_list = [
    {
        'id': encuesta['name'].split('/')[-1],
        'nombre': encuesta['fields']['nombre']['stringValue']
    }
    for encuesta in encuestas if 'nombre' in encuesta['fields']
]
    for encuesta in encuestas:
        encuesta_id = encuesta.get('fields', {}).get('id', {}).get('stringValue', None)
        encuesta_nombre = encuesta.get('fields', {}).get('nombre', {}).get('stringValue', None)

        if encuesta_id and encuesta_nombre:
            encuestas_list.append({'id': encuesta_id, 'nombre': encuesta_nombre})

    return render(request, 'mi_app/difucion/enviar_correos.html', {
        'titulos_eventos': titulos_eventos, 
        'carreras': carreras,
        'encuestas': encuestas_list
    })

FIREBASE_URL = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Misiones"

def listar_misiones(request):
    response = requests.get(FIREBASE_URL)

    if response.status_code == 200:
        misiones = response.json().get('documents', [])
        misiones_data = []
        for mision in misiones:
            mision_id = mision['name'].split('/')[-1]

            mision_data = {
                'id': mision_id,
                'titulo': mision_id,
                'descripcion': mision['fields'].get('descripcion', {}).get('stringValue', 'Sin descripción'),
                'puntaje': mision['fields'].get('puntaje', {}).get('integerValue', 0),
                'objetivo': mision['fields'].get('objetivo', {}).get('stringValue', 'Sin objetivo'),
                'categoria': mision['fields'].get('categoria', {}).get('stringValue', 'Sin categoría'),
                'meta': mision['fields'].get('meta', {}).get('integerValue', 0)
            }
            misiones_data.append(mision_data)

        return render(request, 'mi_app/mision/listar_misiones.html', {'misiones': misiones_data})

    else:
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
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos/{gestor_id}"
    headers = {"Content-Type": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        messages.error(request, "No se pudo encontrar el Gestor.")
        return redirect('gestores')

    gestor_data = response.json()['fields']
    nombre_completo = gestor_data['Nombre_completo']['stringValue']
    rut = gestor_data['rut']['stringValue']
    email = gestor_data['email']['stringValue']
    password = gestor_data['password']['stringValue']

    if request.method == 'POST':
        nuevo_nombre_completo = request.POST.get('nombre_completo')
        nuevo_rut = request.POST.get('rut')
        nuevo_email = request.POST.get('email')
        nuevo_password = request.POST.get('password')

        if not nuevo_nombre_completo or not nuevo_rut or not nuevo_email or not nuevo_password:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'mi_app/gestorCRUD/modificar_gestor.html', {
                'gestor_id': gestor_id,
                'nombre_completo': nombre_completo,
                'rut': rut,
                'email': email,
                'password': password
            })

        payload = {
            "fields": {
                "Nombre_completo": {"stringValue": nuevo_nombre_completo},
                "rut": {"stringValue": nuevo_rut},
                "email": {"stringValue": nuevo_email},
                "password": {"stringValue": nuevo_password},
            }
        }

        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 200:
            messages.success(request, "Gestor de eventos modificado correctamente.")
            return redirect('gestores')
        else:
            messages.error(request, "Error al modificar el Gestor.")

    return render(request, 'mi_app/gestorCRUD/modificar_gestor.html', {
        'gestor_id': gestor_id,
        'nombre_completo': nombre_completo,
        'rut': rut,
        'email': email,
        'password': password
    })

def boceto(request):
    return render(request,'mi_app/boceto.html')

def dashboard(request):
    url_eventos = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    response_eventos = requests.get(url_eventos)
    eventos = []

    if response_eventos.status_code == 200:
        eventos = response_eventos.json().get('documents', [])
        for evento in eventos:
            evento_id = evento['name'].split('/')[-1]
            evento['id'] = evento_id

    url_gestores = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos"
    response_gestores = requests.get(url_gestores)
    gestores = []

    if response_gestores.status_code == 200:
        gestores = response_gestores.json().get('documents', [])
        for gestor in gestores:
            gestor_id = gestor['name'].split('/')[-1]
            gestor['id'] = gestor_id
            gestor['email'] = gestor['fields']['email']['stringValue']

    if request.method == 'POST':
        evento_id = request.POST.get('evento_id')
        gestor_id = request.POST.get('gestor_id')

        gestor_seleccionado = next((g for g in gestores if g['id'] == gestor_id), None)

        if gestor_seleccionado:
            evento_seleccionado = next((e for e in eventos if e['id'] == evento_id), None)

            if evento_seleccionado:
                try:
                    titulo_evento = evento_seleccionado['fields']['titulo']['stringValue']
                    fecha_evento = evento_seleccionado['fields']['fecha']['timestampValue']
                    nombre_gestor = gestor_seleccionado['fields']['Nombre_completo']['stringValue']

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

        return redirect('dashboard')

    return render(request, 'mi_app/dashboard/dashboard.html', {'eventos': eventos, 'gestores': gestores})

url_consultas = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Consultas"

import requests
from django.shortcuts import render, redirect
from django.contrib import messages

def panel_control(request):
    try:
        # Obtener los datos desde Firebase para las consultas
        url_consultas = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Consultas"
        response_consultas = requests.get(url_consultas)
        if response_consultas.status_code != 200:
            print(f"Error en la solicitud de consultas: {response_consultas.status_code} - {response_consultas.text}")
            return render(request, 'mi_app/home.html', {'error': 'Error al obtener las consultas.'})

        # Extraer y procesar documentos de las consultas
        consultas = response_consultas.json().get('documents', [])
        if not consultas:
            print("No hay documentos en la colección de consultas.")
            return render(request, 'mi_app/home.html', {'error': 'No hay consultas disponibles.'})

        consultas_pendientes = []
        for consulta in consultas:
            try:
                estado = consulta['fields']['estado']['stringValue']
                if estado.strip().lower() == "pendiente":
                    consultas_pendientes.append({
                        'id': consulta['name'].split("/")[-1],
                        'correo': consulta['fields']['correo']['stringValue'],
                        'estado': estado,
                        'mensaje': consulta['fields']['mensaje']['stringValue'],
                        'motivo': consulta['fields']['motivo']['stringValue'],
                        'nombre': consulta['fields']['nombre']['stringValue'],
                    })
            except KeyError as e:
                print(f"Campo faltante en la consulta: {e}")

        # Calcular el total y el pendiente de consultas
        total_consultas = len(consultas)
        consultas_pendientes_count = len(consultas_pendientes)

        if total_consultas > 0:
            progreso = (consultas_pendientes_count / total_consultas) * 100
        else:
            progreso = 0  
        if consultas_pendientes_count == 0:
            color_progreso = "blue"  
        else:
            color_progreso = "#ffc107"  

        # Obtener los datos desde Firebase para los eventos
        url_eventos = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
        response_eventos = requests.get(url_eventos)
        if response_eventos.status_code != 200:
            print(f"Error en la solicitud de eventos: {response_eventos.status_code} - {response_eventos.text}")
            return render(request, 'mi_app/home.html', {'error': 'Error al obtener los eventos.'})

        # Extraer y procesar documentos de los eventos
        eventos = response_eventos.json().get('documents', [])
        eventos_sin_gestor = []
        inscritos_por_evento = []  # Aquí vamos a almacenar la cantidad de inscritos por evento

        for evento in eventos:
            try:
                gestor = evento['fields']['gestor']['stringValue']
                inscritos = evento['fields']['inscritos']['integerValue']
                titulo = evento['fields']['titulo']['stringValue']

                if gestor.strip().lower() == "sin gestor":
                    eventos_sin_gestor.append({
                        'id_evento': evento['name'].split("/")[-1],  # Aquí obtenemos el ID del evento
                        'titulo': titulo,
                        'descripcion': evento['fields']['descripcion']['stringValue'],
                        'fecha': evento['fields']['fecha']['timestampValue'],
                        'lugar': evento['fields']['lugar']['stringValue'],
                        'cupos': evento['fields']['Cupos']['integerValue'],
                    })
                
                # Guardamos la cantidad de inscritos por evento
                inscritos_por_evento.append({
                    'titulo': titulo,
                    'inscritos': inscritos,
                })
            except KeyError as e:
                print(f"Campo faltante en el evento: {e}")

        # Calcular el total de eventos sin gestor
        total_eventos = len(eventos)
        eventos_sin_gestor_count = len(eventos_sin_gestor)

        # Calcular el progreso de los eventos sin gestor
        if total_eventos > 0:
            progreso_eventos = (eventos_sin_gestor_count / total_eventos) * 100
        else:
            progreso_eventos = 0

        # Obtener los datos desde Firebase para GestorEventos
        url_gestor_eventos = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos"
        response_gestor_eventos = requests.get(url_gestor_eventos)
        if response_gestor_eventos.status_code != 200:
            print(f"Error en la solicitud de GestorEventos: {response_gestor_eventos.status_code} - {response_gestor_eventos.text}")
            return render(request, 'mi_app/home.html', {'error': 'Error al obtener los gestores.'})

        # Extraer y procesar documentos de los GestorEventos
        gestores = response_gestor_eventos.json().get('documents', [])
        gestores_nombre_completo = []

        for gestor in gestores:
            try:
                nombre_completo = gestor['fields']['Nombre_completo']['stringValue']
                gestores_nombre_completo.append({
                    'id': gestor['name'].split("/")[-1],  # Obtener el ID del gestor
                    'nombre_completo': nombre_completo,
                })
            except KeyError as e:
                print(f"Campo faltante en el gestor: {e}")

        # Si el formulario se envía para crear una tarea de gestor
        if request.method == 'POST':
            evento_id = request.POST.get('evento_id')
            gestor_id = request.POST.get('gestor_id')

            if evento_id and gestor_id:
                try:
                    # Obtener el nombre completo del gestor seleccionado
                    url_gestor = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/GestorEventos/{gestor_id}"
                    response_gestor = requests.get(url_gestor)

                    if response_gestor.status_code != 200:
                        return render(request, 'mi_app/home.html', {'error': 'Error al obtener los detalles del gestor.'})

                    gestor = response_gestor.json().get('fields', {})
                    nombre_completo = gestor.get('Nombre_completo', {}).get('stringValue')

                    # Crear un nuevo documento en la colección TareasGestor con la relación entre el evento y el gestor
                    url_tareas_gestor = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/TareasGestor"
                    data_tarea = {
                        "fields": {
                            "evento_id": {"stringValue": evento_id},  # Usamos el ID del evento que se pasa en el formulario
                            "gestor_id": {"stringValue": gestor_id},  # Usamos el ID del gestor seleccionado
                            "gestor_nombre_completo": {"stringValue": nombre_completo}  # Nombre del gestor seleccionado
                        }
                    }

                    response_create_tarea = requests.post(url_tareas_gestor, json=data_tarea)

                    if response_create_tarea.status_code == 200:
                        messages.success(request, f'Gestor asignado correctamente al evento.')
                    else:
                        messages.error(request, 'Error al asignar el gestor al evento.')
                except Exception as e:
                    print(f"Error al asignar gestor: {e}")
                    messages.error(request, 'Error al asignar el gestor al evento.')

            # Redirigir a la misma página después de procesar la asignación
            return redirect('panel_control')

        # Enviar los datos a la plantilla
        return render(request, 'mi_app/panel-control/panel-control.html', {
            'consultas_pendientes_count': consultas_pendientes_count,
            'total_consultas': total_consultas,
            'progreso': progreso,
            'color_progreso': color_progreso,
            'consultas_pendientes': consultas_pendientes,
            'eventos_sin_gestor': eventos_sin_gestor,
            'total_eventos': total_eventos,
            'eventos_sin_gestor_count': eventos_sin_gestor_count,
            'progreso_eventos': progreso_eventos,
            'inscritos_por_evento': inscritos_por_evento,  # Pasamos la lista de inscritos por evento
            'gestores_nombre_completo': gestores_nombre_completo  # Pasamos la lista de gestores
        })

    except Exception as e:
        print(f"Error inesperado: {e}")
        return render(request, 'mi_app/panel-control/panel-control.html', {'error': 'Error interno al obtener los datos.'})



def responder_consulta(request, consulta_id):
    from datetime import datetime
    import pytz
    import requests

    try:
        consulta_url = f"{url_consultas}/{consulta_id}"
        consulta_response = requests.get(consulta_url)

        if consulta_response.status_code != 200:
            raise Exception("Error al obtener la consulta.")

        consulta = consulta_response.json()

        consulta_data = {
            "correo": consulta['fields']['correo']['stringValue'],
            "nombre": consulta['fields']['nombre']['stringValue'],
            "motivo": consulta['fields']['motivo']['stringValue'],
            "mensaje": consulta['fields']['mensaje']['stringValue'],
            "timestamp": consulta['fields']['timestamp']['timestampValue']
        }

    except Exception as e:
        print(f"Error al obtener datos de la consulta: {e}")
        return render(request, 'mi_app/consultas/responder_consulta.html', {'error': 'No se pudo obtener la consulta.'})

    if request.method == "POST":
        respuesta = request.POST.get('respuesta', '')

        try:
            mensaje_correo = f"Hola {consulta_data['nombre']},\n\nTu consulta con el motivo de '{consulta_data['motivo']}' ha sido leída y está siendo respondida a continuación:\n\n{respuesta}"

            send_mail(
                subject=f"Respuesta a tu consulta sobre '{consulta_data['motivo']}'",
                message=mensaje_correo,
                from_email="punto.estudiantil.puntoduoc@gmail.com",
                recipient_list=[consulta_data['correo']],
            )

            respuesta_timestamp = datetime.now(pytz.timezone('America/Santiago')).isoformat()

            data_actualizada = {
                "fields": {
                    "estado": {"stringValue": "Respondido"},
                    "respuesta_admin": {"stringValue": respuesta},
                    "respuesta_timestamp": {"timestampValue": respuesta_timestamp},
                    "correo": {"stringValue": consulta_data['correo']},
                    "nombre": {"stringValue": consulta_data['nombre']},
                    "motivo": {"stringValue": consulta_data['motivo']},
                    "mensaje": {"stringValue": consulta_data['mensaje']},
                    "timestamp": {"timestampValue": consulta_data['timestamp']},
                }
            }
            actualizar_response = requests.patch(consulta_url, json=data_actualizada)
            if actualizar_response.status_code not in [200, 204]:
                raise Exception("Error al actualizar la consulta en Firebase.")

            return redirect('listar_consultas')

        except Exception as e:
            print(f"Error al responder consulta: {e}")
            return render(request, 'mi_app/consultas/responder_consulta.html', {
                'error': 'Error al procesar la consulta.',
                'consulta': consulta_data
            })

    return render(request, 'mi_app/consultas/responder_consulta.html', {
        'consulta': consulta_data
    })

def home (request):
    return render(request,'mi_app/home.html')


