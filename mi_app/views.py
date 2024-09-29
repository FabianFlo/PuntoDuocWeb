from django.http import JsonResponse
from django.shortcuts import render, redirect
import requests
from datetime import datetime


def index(request):
    if request.method == 'POST':
        campo1 = request.POST.get('campo1')
        campo2 = request.POST.get('campo2')

        # URL para agregar un nuevo documento a la colección "pruebas"
        url = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/pruebas"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "fields": {
                "campo1": {"stringValue": campo1},
                "campo2": {"stringValue": campo2},
            }
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            print("Datos subidos a Firestore correctamente.")
        else:
            print("Error al subir datos a Firestore:", response.content)
        return redirect('index') 

    return render(request, 'mi_app/index.html')


def format_fecha(fecha):
    try:
        return datetime.strptime(fecha, '%d/%m/%Y').isoformat() + 'Z'
    except ValueError:
        print("Formato de fecha no válido:", fecha)
        return None  # Maneja el caso de formato no válido
    
def subir_evento_view(request):
    if request.method == 'POST':
        datos = {
            'descripcion': request.POST.get('descripcion'),
            'estado': request.POST.get('estado'),
            'fecha': format_fecha(request.POST.get('fecha')),
            'fecha_creacion': format_fecha(request.POST.get('fecha_creacion')),
            'imagen': request.POST.get('imagen'),
            'lugar': request.POST.get('lugar'),
            'sede': request.POST.get('sede'),
            'tipo': request.POST.get('tipo'),
            'titulo': request.POST.get('titulo')
        }

        # Verifica si las fechas son válidas antes de continuar
        if datos['fecha'] is None or datos['fecha_creacion'] is None:
            return JsonResponse({'error': 'Formato de fecha no válido'}, status=400)

        # URL de Firestore
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
        else:
            print("Error al subir datos a Firestore:", response.content)

        return JsonResponse({'message': 'Evento subido correctamente'}, status=200)

    return render(request, 'mi_app/subir_evento.html')
