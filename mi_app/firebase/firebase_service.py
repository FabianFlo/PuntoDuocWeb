import requests
import json

# Variables de configuración
FIREBASE_API_KEY = "AIzaSyDo7PfmgYR63N_f-_QGxJsY-BeDFjWWd3E"
FIREBASE_PROJECT_ID = "puntoduoc-894e9"
FIREBASE_URL = f'https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/'

# Función para subir datos
def subir_datos(coleccion, datos):
    url = f'{FIREBASE_URL}{coleccion}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {FIREBASE_API_KEY}'  # Cambia esto si necesitas un token diferente
    }
    response = requests.post(url, headers=headers, json=datos)
    print(response.json())  # Imprime la respuesta de Firestore

# Ejemplo de uso
if __name__ == "__main__":
    datos = {
        'campo1': 'valor1',
        'campo2': 'valor2'
    }
    coleccion = 'si'  # Reemplaza con el nombre de tu colección
    subir_datos(coleccion, datos)
