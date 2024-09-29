from django.shortcuts import render, redirect
import requests

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

        # Hacer la solicitud POST para agregar el documento
        response = requests.post(url, headers=headers, json=data)

        # Verificar si la solicitud fue exitosa
        if response.status_code in [200, 201]:
            print("Datos subidos a Firestore correctamente.")
        else:
            print("Error al subir datos a Firestore:", response.content)

        return redirect('index')  # Redirige a la misma página después de subir los datos

    return render(request, 'mi_app/index.html')
