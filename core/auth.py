"""
Autenticación propia del proyecto. No se usa django.contrib.auth porque ese
sistema necesita el ORM y una base de datos SQL, y este proyecto solo usa
MongoDB vía PyMongo.

El "login" guarda los datos del usuario en request.session (cookie firmada,
ver SESSION_ENGINE en settings.py) después de validar el password con
werkzeug. login_requerido y admin_requerido son decoradores que chequean esa
misma sesión para proteger vistas.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect, render
from werkzeug.security import check_password_hash, generate_password_hash

from core.db import get_db
from core.forms import LoginForm, RegistroForm
from core.utils import siguiente_sql_id


def login_view(request):
    if request.session.get('user_id'):
        return redirect('inicio')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        db = get_db()
        email = form.cleaned_data['email'].strip().lower()
        password = form.cleaned_data['password']

        usuario = db.usuarios.find_one({'email': email})
        if usuario and check_password_hash(usuario.get('password', ''), password):
            # Guardamos solo lo necesario en sesión, no el documento completo.
            request.session['user_id'] = usuario['sql_id']
            request.session['user_nombre'] = usuario.get('nombre', '')
            request.session['user_email'] = usuario.get('email', '')
            request.session['user_rol'] = usuario.get('rol', 'usuario')
            request.session['user_tipo'] = usuario.get('tipo', 'Free')
            messages.success(request, f"¡Bienvenido/a, {usuario.get('nombre', '')}!")
            return redirect('inicio')

        messages.error(request, 'Email o contraseña incorrectos.')

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('login')


def registro_view(request):
    if request.session.get('user_id'):
        return redirect('inicio')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        db = get_db()
        email = form.cleaned_data['email'].strip().lower()

        if db.usuarios.find_one({'email': email}):
            form.add_error('email', 'Ya existe una cuenta con ese email.')
        else:
            nuevo_id = siguiente_sql_id(db.usuarios)
            db.usuarios.insert_one({
                'sql_id': nuevo_id,
                'nombre': form.cleaned_data['nombre'].strip(),
                'email': email,
                'password': generate_password_hash(form.cleaned_data['password']),
                'rol': 'usuario',
                'tipo': 'Free',
                'suscripcion': {'tipo': 'Free', 'estado': 'Activa'},
                'artistas_seguidos': [],
                'canciones_liked': [],
            })
            messages.success(request, 'Cuenta creada con éxito. Ya podés iniciar sesión.')
            return redirect('login')

    return render(request, 'auth/registro.html', {'form': form})


def login_requerido(vista):
    """Exige que haya alguien logueado (cualquier rol) para acceder a la vista."""
    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.warning(request, 'Iniciá sesión para continuar.')
            return redirect('login')
        return vista(request, *args, **kwargs)
    return wrapper


def admin_requerido(vista):
    """Exige sesión iniciada Y rol admin para acceder a la vista."""
    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.warning(request, 'Iniciá sesión para continuar.')
            return redirect('login')
        if request.session.get('user_rol') != 'admin':
            messages.error(request, 'No tenés permisos para acceder a esa sección.')
            return redirect('inicio')
        return vista(request, *args, **kwargs)
    return wrapper
