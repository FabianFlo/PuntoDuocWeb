from django.shortcuts import render, redirect
from django.contrib import messages
import requests

# URL de Firestore
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Encuestas"

def crear_encuesta(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')

        # Crear una estructura para la encuesta
        encuesta_data = {
            'nombre': nombre,
            'preguntas': []
        }

        # Obtener preguntas y sus tipos
        for i in range(len(request.POST.getlist('pregunta'))):
            pregunta = request.POST.getlist('pregunta')[i]
            tipo = request.POST.getlist('tipo')[i]
            opciones = request.POST.getlist('opciones')  # Obtener todas las opciones

            # Filtrar las opciones no vacías
            if tipo == 'opciones':
                opciones = [opcion.strip() for opcion in opciones if opcion.strip()]

            encuesta_data['preguntas'].append({
                'pregunta': pregunta,
                'tipo': tipo,
                'opciones': [{'opcion': opcion} for opcion in opciones]  # Cambiar a diccionario simple
            })

        # Agregar preguntas adicionales
        encuesta_data['preguntas'].append({
            'pregunta': '¿De qué carrera vienes?',
            'tipo': 'texto',  # Asumimos que es un tipo de texto
            'opciones': []
        })
        
        encuesta_data['preguntas'].append({
            'pregunta': '¿A qué eventos asististe?',
            'tipo': 'texto',  # Asumimos que es un tipo de texto
            'opciones': []
        })

        # Preparar el JSON para enviar a Firestore
        firestore_data = {
            'fields': {
                'nombre': {'stringValue': nombre},
                'preguntas': {
                    'arrayValue': {
                        'values': [
                            {
                                'mapValue': {
                                    'fields': {
                                        'pregunta': {'stringValue': pregunta['pregunta']},
                                        'tipo': {'stringValue': pregunta['tipo']},
                                        'opciones': {
                                            'arrayValue': {
                                                'values': [
                                                    {'mapValue': {'fields': {'opcion': {'stringValue': opcion['opcion']}}}} for opcion in pregunta['opciones']
                                                ]
                                            }
                                        }
                                    }
                                }
                            } for pregunta in encuesta_data['preguntas']
                        ]
                    }
                }
            }
        }

        # Enviar a Firestore
        response = requests.post(FIRESTORE_URL, json=firestore_data)

        if response.status_code == 200:
            messages.success(request, "Encuesta creada exitosamente.")
            return redirect('ver_encuestas')
        else:
            messages.error(request, "Error al crear la encuesta en Firebase: " + response.text)

    return render(request, 'encuestas/crear_encuesta.html')


def ver_encuestas(request):
    response = requests.get(FIRESTORE_URL)
    encuestas = []

    if response.status_code == 200:
        data = response.json()
        for doc in data.get('documents', []):
            fields = doc['fields']
            encuesta = {
                'id': doc['name'].split('/')[-1],
                'nombre': fields.get('nombre', {}).get('stringValue', ''),
                'preguntas': [
                    {
                        'pregunta': pregunta['mapValue']['fields'].get('pregunta', {}).get('stringValue', ''),
                        'tipo': pregunta['mapValue']['fields'].get('tipo', {}).get('stringValue', ''),
                        'opciones': [
                            opcion['mapValue']['fields']['opcion']['stringValue']
                            for opcion in pregunta['mapValue']['fields'].get('opciones', {}).get('arrayValue', {}).get('values', [])
                        ]
                    }
                    for pregunta in fields.get('preguntas', {}).get('arrayValue', {}).get('values', [])
                ]
            }
            encuestas.append(encuesta)
    else:
        messages.error(request, "Error al obtener las encuestas.")

    return render(request, 'encuestas/ver_encuestas.html', {'encuestas': encuestas})


def responder_encuesta(request, encuesta_id):
    # Obtener la encuesta de Firestore
    encuesta_url = f"{FIRESTORE_URL}/{encuesta_id}"
    response = requests.get(encuesta_url)

    if response.status_code == 200:
        data = response.json()
        fields = data['fields']
        encuesta = {
            'id': encuesta_id,
            'nombre': fields.get('nombre', {}).get('stringValue', ''),
            'preguntas': [
                {
                    'pregunta': pregunta['mapValue']['fields'].get('pregunta', {}).get('stringValue', ''),
                    'tipo': pregunta['mapValue']['fields'].get('tipo', {}).get('stringValue', ''),
                    'opciones': [
                        opcion['mapValue']['fields']['opcion']['stringValue']
                        for opcion in pregunta['mapValue']['fields'].get('opciones', {}).get('arrayValue', {}).get('values', [])
                    ]
                }
                for pregunta in fields.get('preguntas', {}).get('arrayValue', {}).get('values', [])
            ]
        }
    else:
        messages.error(request, "Encuesta no encontrada.")
        return redirect('ver_encuestas')

    if request.method == 'POST':
        respuestas = {}
        for pregunta in encuesta['preguntas']:
            pregunta_id = pregunta['pregunta']
            respuesta = request.POST.get(pregunta_id)
            respuestas[pregunta_id] = respuesta

        # Guardar las respuestas en Firestore en una colección de respuestas
        respuestas_url = f"https://firestore.googleapis.com/v1/projects/puntoduoc-894e9/databases/(default)/documents/Encuestas/{encuesta_id}/Respuestas"
        data = {
            'fields': {
                'respuestas': {
                    'mapValue': {
                        'fields': {key: {'stringValue': value} for key, value in respuestas.items()}
                    }
                }
            }
        }

        response = requests.post(respuestas_url, json=data)

        if response.status_code in [200, 201]:  # Aceptar respuestas 200 o 201
            messages.success(request, "Respuestas enviadas exitosamente.")
        else:
            messages.error(request, "Error al enviar las respuestas: " + response.text)

        return redirect('ver_encuestas')

    return render(request, 'encuestas/responder_encuesta.html', {'encuesta': encuesta})
