from django.contrib import messages
from django.shortcuts import render, redirect
import requests
from datetime import datetime
import uuid

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
            'cupos': request.POST.get('cupos'),
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
            "Cupos": {"integerValue": datos['cupos']},
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
            'cupos': request.POST.get('cupos'),
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
            "Cupos": {"integerValue": datos['cupos']},
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
