from django.http import JsonResponse
from django.shortcuts import render, redirect
import requests
from datetime import datetime
import uuid  # Importamos uuid para generar un identificador único


import requests
from django.shortcuts import render

# mi_app/views.py

def metricas_view(request):
    # URL de Firestore para la colección "Eventos"
    eventos_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
    
    # URL de Firestore para la colección "Estudiantes"
    estudiantes_url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/estudiantes"
    
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

    return render(request, 'mi_app/metricas/metricas.html', {'eventos': context})
    #return render(request, 'mi_app/metricas.html', context)

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
        # Generar el ID del evento
        id_evento = str(uuid.uuid4())  

        # Esto es para traer los datos del form por: id y el name control form
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
            'cupos': request.POST.get('cupos'),
        }

        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Eventos"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Llevar los datos al Firebase
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
            "Cupos": {"integerValue": datos['cupos']},
            "inscritos": {"integerValue": "0"},  # Inicializamos en 0
            "listaEspera": {
                "arrayValue": {
                    "values": []  # Inicializamos con un array vacío
                }
            }
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
            'titulo': request.POST.get('titulo'),
            'cupos': request.POST.get('cupos'),
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
            "titulo": {"stringValue": datos['titulo']},
            "Cupos": {"integerValue": datos['cupos']},
            "inscritos": {"integerValue": "0"},  # Inicializamos en 0
                "listaEspera": {
                    "arrayValue": {
                        "values": []  # Inicializamos con un array vacío
                    }
                }
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
        id_estudiante = str(uuid.uuid4())  
        
        datos = {
            'nombre_completo': request.POST.get('nombre_completo'),
            'rut': request.POST.get('rut'),
            'telefono': request.POST.get('telefono'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'carrera': request.POST.get('carrera'),
        }

        # URL de Firestore para la colección de estudiantes
        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
        headers = {
            "Content-Type": "application/json"
        }

        # Subir los datos a Firestore
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
            "eventosInscritos": {
                "arrayValue": {
                    "values": []  # Inicializamos con un array vacío
                }
            }
        }})

        if response.status_code in [200, 201]:
            alert_message = "Estudiante creado correctamente."
        else:
            alert_message = "Error al crear el estudiante."

        return render(request, 'mi_app/estudiantesCRUD/crear_estudiante.html', {'alert_message': alert_message})

    return render(request, 'mi_app/estudiantesCRUD/crear_estudiante.html')

def listar_estudiantes_view(request):
    # URL de Firestore para la colección "estudiantes"
    url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes"
    
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
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes/{estudiante_id}"

    if request.method == "POST":
        response = requests.delete(url)

        if response.status_code == 204:  # 204 No Content significa que se eliminó correctamente
            print("Estudiante eliminado correctamente.")
        else:
            print("Error al eliminar el estudiante.")

    return redirect('listar_estudiantes')

def modificar_estudiante_view(request, estudiante_id):
    # URL para obtener el estudiante a modificar
    url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Estudiantes/{estudiante_id}"
    
    if request.method == "POST":
        # Obtener los datos del formulario
        datos = {
            'Nombre_completo': request.POST.get('nombre_completo'),
            'Rut': request.POST.get('rut'),
            'Telefono': request.POST.get('telefono'),
            'email': request.POST.get('email'),
            'id_estudiante': estudiante_id,  
            'password': request.POST.get('password'),
            'carrera': request.POST.get('carrera'),
            'puntaje': request.POST.get('puntaje')
        }
        
        # Convertir el puntaje a entero si es posible
        if datos['puntaje']:
            datos['puntaje'] = int(datos['puntaje'])
        else:
            datos['puntaje'] = 0  # O algún valor por defecto si es necesario

        fields = {}
        if datos['Nombre_completo']:
            fields["Nombre_completo"] = {"stringValue": datos['Nombre_completo']}
        if datos['Rut']:
            fields["Rut"] = {"stringValue": datos['Rut']}
        if datos['Telefono']:
            fields["Telefono"] = {"stringValue": datos['Telefono']}
        if datos['email']:
            fields["email"] = {"stringValue": datos['email']}
        if datos['id_estudiante']:
            fields["id_estudiante"] = {"stringValue": datos['id_estudiante']}
        if datos['password']:
            fields["password"] = {"stringValue": datos['password']}
        if datos['carrera']:
            fields["carrera"] = {"stringValue": datos['carrera']}
        if datos['puntaje'] is not None:
            fields["puntaje"] = {"integerValue": datos['puntaje']}

        response = requests.patch(url, json={"fields": fields})

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
