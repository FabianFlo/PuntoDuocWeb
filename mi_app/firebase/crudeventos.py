import requests
import json
from datetime import datetime

# Variables de configuración
FIREBASE_API_KEY = "AIzaSyDo7PfmgYR63N_f-_QGxJsY-BeDFjWWd3E"
FIREBASE_PROJECT_ID = "puntoduoc-894e9"
FIREBASE_URL = f'https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/'

# Función para subir datos a la colección "Eventos"
def subir_evento(datos):
    url = f'{FIREBASE_URL}Eventos'  # Colección "Eventos"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {FIREBASE_API_KEY}'
    }
    response = requests.post(url, headers=headers, json=datos)
    print(response.json())  # Imprime la respuesta de Firestore

# Ejemplo de uso

