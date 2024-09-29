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