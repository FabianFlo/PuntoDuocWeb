from django.http import JsonResponse
from django.shortcuts import render, redirect
import requests
from datetime import datetime

def format_fecha(fecha):
    if fecha:
        try:
            # Parsear la fecha del input y formatearla al estilo ISO 8601 con 'Z' para UTC
            fecha_formateada = datetime.fromisoformat(fecha).strftime('%Y-%m-%dT%H:%M:%SZ')
            return fecha_formateada
        except ValueError:
            # Si ocurre un error en el formato de la fecha, usar la fecha actual
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        # Si no se pasa una fecha, usar la fecha actual en formato UTC
        return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
# # #  esto es el crud de los eventos
def subir_evento_view(request):
    if request.method == 'POST':
        datos = {
            'descripcion': request.POST.get('descripcion'),
            'estado': request.POST.get('estado'),
            'fecha': format_fecha(request.POST.get('fecha')),
            'fecha_creacion': format_fecha(None),
            'imagen': request.POST.get('imagen'),
            'lugar': request.POST.get('lugar'),
            'sede': request.POST.get('sede'),
            'tipo': request.POST.get('tipo'),
            'titulo': request.POST.get('titulo')
        }

        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={"fields": {
            "descripcion": {"stringValue": datos['descripcion']},
            "estado": {"stringValue": datos['estado']},
            "fecha": {"timestampValue": datos['fecha']},
            "fecha_creacion": {"timestampValue": datos['fecha_creacion']},
            "imagen": {"stringValue": datos['imagen']},
            "lugar": {"stringValue": datos['lugar']},
            "sede": {"stringValue": datos['sede']},
            "tipo": {"stringValue": datos['tipo']},
            "titulo": {"stringValue": datos['titulo']}
        }})

        if response.status_code in [200, 201]:
            print("Evento subido a Firestore correctamente.")
            alert_message = "Evento subido correctamente"
        else:
            print("Error al subir datos a Firestore:", response.content)
            alert_message = "Error al subir evento"

        return render(request, 'mi_app/eventosCRUD/subir_evento.html', {'alert_message': alert_message})

    return render(request, 'mi_app/eventosCRUD/subir_evento.html')

def listar_eventos_view(request):
    url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    
    response = requests.get(url)
    
    eventos = []
    if response.status_code == 200:
        eventos = response.json().get('documents', [])
        for evento in eventos:
            evento_id = evento['name'].split('/')[-1]  # Extraer solo el ID
            evento['id'] = evento_id  # Añadir el ID al evento

    return render(request, 'mi_app/eventosCRUD/listar_eventos.html', {'eventos': eventos})

def eliminar_evento_view(request, evento_id):
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos/{evento_id}"

    if request.method == "POST":
        response = requests.delete(url)

        if response.status_code == 204:  # 204 No Content significa que se eliminó correctamente
            return redirect('listar_eventos')  # Redirigir a la lista de eventos
        else:
            print("Error al eliminar el evento:", response.content)

    return redirect('listar_eventos')

def modificar_evento_view(request, evento_id):
    # URL de Firestore para obtener el evento
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos/{evento_id}"
    
    if request.method == 'GET':
        # Obtener los datos del evento para prellenar el formulario
        response = requests.get(url)
        if response.status_code == 200:
            evento = response.json()['fields']
            return render(request, 'mi_app/eventosCRUD/evento_modificar.html', {'evento': evento})
        else:
            print("Error al obtener los datos del evento:", response.content)
            return redirect('listar_eventos')
    
    elif request.method == 'POST':
        # Datos que serán enviados para modificar el evento
        datos = {
            'descripcion': request.POST.get('descripcion'),
            'estado': request.POST.get('estado'),
            'fecha': format_fecha(request.POST.get('fecha')),  # Formatea la fecha
            'imagen': request.POST.get('imagen'),
            'lugar': request.POST.get('lugar'),
            'sede': request.POST.get('sede'),
            'tipo': request.POST.get('tipo'),
            'titulo': request.POST.get('titulo')
        }
        
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.patch(url, headers=headers, json={"fields": {
            "descripcion": {"stringValue": datos['descripcion']},
            "estado": {"stringValue": datos['estado']},
            "fecha": {"timestampValue": datos['fecha']},  # Usa el formato de fecha correcto
            "imagen": {"stringValue": datos['imagen']},
            "lugar": {"stringValue": datos['lugar']},
            "sede": {"stringValue": datos['sede']},
            "tipo": {"stringValue": datos['tipo']},
            "titulo": {"stringValue": datos['titulo']}
        }})

        if response.status_code in [200, 204]:
            alert_message = "Evento modificado correctamente"
            return render(request, 'mi_app/eventosCRUD/evento_modificar.html', {'alert_message': alert_message, 'evento': datos})
        else:
            print("Error al modificar el evento:", response.content)
            return render(request, 'mi_app/eventosCRUD/evento_modificar.html', {'alert_message': 'Error al modificar evento'})
# # #  home      
def home_view(request):
    return render(request, 'mi_app/home.html')
# # # esto CRUD estudantes
def crear_estudiante_view(request):
    if request.method == 'POST':
        datos = {
            'nombre_completo': request.POST.get('nombre_completo'),
            'rut': request.POST.get('rut'),
            'telefono': request.POST.get('telefono'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'id_estudiante': ''  # Lo generaremos después de subir el estudiante
        }

        # URL de Firestore para la colección de estudiantes
        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/estudiantes"
        headers = {
            "Content-Type": "application/json"
        }

        # Subir los datos a Firestore
        response = requests.post(url, headers=headers, json={"fields": {
            "Nombre_completo": {"stringValue": datos['nombre_completo']},
            "Rut": {"stringValue": datos['rut']},
            "Telefono": {"stringValue": datos['telefono']},
            "email": {"stringValue": datos['email']},
            "password": {"stringValue": datos['password']}
        }})

        if response.status_code in [200, 201]:
            alert_message = "Estudiante creado correctamente."
        else:
            alert_message = "Error al crear el estudiante."

        return render(request, 'mi_app/estudiantesCRUD/crear_estudiante.html', {'alert_message': alert_message})

    return render(request, 'mi_app/estudiantesCRUD/crear_estudiante.html')

def listar_estudiantes_view(request):
    # URL de Firestore para la colección "estudiantes"
    url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/estudiantes"
    
    # Realiza la solicitud para obtener los estudiantes
    response = requests.get(url)
    
    estudiantes = []
    if response.status_code == 200:
        estudiantes = response.json().get('documents', [])
        # Añadir el ID del documento (Firestore) a los datos del estudiante
        for estudiante in estudiantes:
            estudiante_id = estudiante['name'].split('/')[-1]  # Extraer solo el ID del documento
            estudiante['id'] = estudiante_id  # Añadir el ID a los datos del estudiante

    return render(request, 'mi_app/estudiantesCRUD/listar_estudiantes.html', {'estudiantes': estudiantes})

def eliminar_estudiante_view(request, estudiante_id):
    # URL de Firestore para eliminar el estudiante
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/estudiantes/{estudiante_id}"

    if request.method == "POST":
        response = requests.delete(url)

        if response.status_code == 204:  # 204 No Content significa que se eliminó correctamente
            print("Estudiante eliminado correctamente.")
        else:
            print("Error al eliminar el estudiante.")

    return redirect('listar_estudiantes')

def modificar_estudiante_view(request, estudiante_id):
    # URL para obtener el estudiante a modificar
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/estudiantes/{estudiante_id}"
    
    if request.method == "POST":
        # Obtener los datos del formulario
        datos = {
            'Nombre_completo': request.POST.get('Nombre_completo'),
            'Rut': request.POST.get('Rut'),
            'Telefono': request.POST.get('Telefono'),
            'email': request.POST.get('email'),
            'id_estudiante': estudiante_id,  # Usar el ID del estudiante
            'password': request.POST.get('password')
        }
        
        # Enviar los datos actualizados a Firestore
        response = requests.patch(url, json={"fields": {
            "Nombre_completo": {"stringValue": datos['Nombre_completo']},
            "Rut": {"stringValue": datos['Rut']},
            "Telefono": {"stringValue": datos['Telefono']},
            "email": {"stringValue": datos['email']},
            "id_estudiante": {"stringValue": datos['id_estudiante']},
            "password": {"stringValue": datos['password']}
        }})

        if response.status_code in [200, 204]:
            return redirect('listar_estudiantes')  # Redirigir a la lista de estudiantes
        else:
            print("Error al modificar el estudiante:", response.content)

    # Obtener los datos actuales del estudiante
    response = requests.get(url)
    if response.status_code == 200:
        estudiante = response.json().get('fields', {})
        return render(request, 'mi_app/estudiantesCRUD/modificar_estudiante.html', {'estudiante': estudiante})

    return redirect('listar_estudiantes')  # Si hay un error, redirigir