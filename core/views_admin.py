"""
Vistas del rol "admin": dashboard global, CRUD de usuarios/canciones/artistas,
listados de todas las playlists/reproducciones y reportes con aggregate de
PyMongo. Todas protegidas con @admin_requerido (core/auth.py).
"""
import re

from django.contrib import messages
from django.shortcuts import redirect, render
from werkzeug.security import generate_password_hash

from core.auth import admin_requerido
from core.db import get_db
from core.forms import ArtistaForm, CancionForm, UsuarioCrearForm, UsuarioForm
from core.utils import siguiente_sql_id

CANCIONES_POR_PAGINA = 20


@admin_requerido
def dashboard(request):
    db = get_db()
    contexto = {
        'total_usuarios': db.usuarios.count_documents({}),
        'total_canciones': db.canciones.count_documents({}),
        'total_artistas': db.artistas.count_documents({}),
        'total_playlists': db.playlists.count_documents({}),
        'total_reproducciones': db.reproducciones.count_documents({}),
        'usuarios_free': db.usuarios.count_documents({'tipo': 'Free'}),
        'usuarios_premium': db.usuarios.count_documents({'tipo': 'Premium'}),
        'top_canciones': list(db.canciones.find().sort('total_reproducciones', -1).limit(5)),
    }
    return render(request, 'admin/dashboard.html', contexto)


# ---------------------------------------------------------------- Usuarios

@admin_requerido
def usuarios_lista(request):
    db = get_db()
    usuarios = list(db.usuarios.find().sort('nombre', 1))
    for u in usuarios:
        u['suscripcion_estado'] = u.get('suscripcion', {}).get('estado', '—')
    return render(request, 'admin/usuarios.html', {'usuarios': usuarios})


@admin_requerido
def usuario_crear(request):
    db = get_db()
    form = UsuarioCrearForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        if db.usuarios.find_one({'email': email}):
            form.add_error('email', 'Ya existe un usuario con ese email.')
        else:
            nuevo_id = siguiente_sql_id(db.usuarios)
            db.usuarios.insert_one({
                'sql_id': nuevo_id,
                'nombre': form.cleaned_data['nombre'].strip(),
                'email': email,
                'password': generate_password_hash(form.cleaned_data['password']),
                'rol': form.cleaned_data['rol'],
                'tipo': form.cleaned_data['tipo'],
                'suscripcion': {
                    'tipo': form.cleaned_data['tipo'],
                    'estado': form.cleaned_data['suscripcion_estado'],
                },
                'artistas_seguidos': [],
                'canciones_liked': [],
            })
            messages.success(request, 'Usuario creado.')
            return redirect('admin_usuarios')

    return render(request, 'admin/usuario_form.html', {'form': form, 'modo': 'crear'})


@admin_requerido
def usuario_editar(request, sql_id):
    db = get_db()
    usuario = db.usuarios.find_one({'sql_id': sql_id})
    if not usuario:
        messages.error(request, 'Ese usuario no existe.')
        return redirect('admin_usuarios')

    suscripcion = usuario.get('suscripcion', {})
    form = UsuarioForm(request.POST or None, initial={
        'nombre': usuario.get('nombre', ''),
        'email': usuario.get('email', ''),
        'tipo': usuario.get('tipo', 'Free'),
        'rol': usuario.get('rol', 'usuario'),
        'suscripcion_estado': suscripcion.get('estado', 'Activa'),
    })

    if request.method == 'POST' and form.is_valid():
        nuevo_email = form.cleaned_data['email'].strip().lower()
        otro = db.usuarios.find_one({'email': nuevo_email, 'sql_id': {'$ne': sql_id}})
        if otro:
            form.add_error('email', 'Ya hay otro usuario con ese email.')
        else:
            db.usuarios.update_one({'sql_id': sql_id}, {'$set': {
                'nombre': form.cleaned_data['nombre'].strip(),
                'email': nuevo_email,
                'tipo': form.cleaned_data['tipo'],
                'rol': form.cleaned_data['rol'],
                'suscripcion.tipo': form.cleaned_data['tipo'],
                'suscripcion.estado': form.cleaned_data['suscripcion_estado'],
            }})
            messages.success(request, 'Usuario actualizado.')
            return redirect('admin_usuarios')

    return render(request, 'admin/usuario_form.html', {'form': form, 'modo': 'editar', 'usuario': usuario})


@admin_requerido
def usuario_eliminar(request, sql_id):
    if request.method != 'POST':
        return redirect('admin_usuarios')

    if sql_id == request.session.get('user_id'):
        messages.error(request, 'No podés eliminar tu propio usuario mientras estás logueado con él.')
        return redirect('admin_usuarios')

    db = get_db()
    db.usuarios.delete_one({'sql_id': sql_id})
    messages.success(request, 'Usuario eliminado.')
    return redirect('admin_usuarios')


# --------------------------------------------------------------- Canciones

@admin_requerido
def canciones_lista(request):
    db = get_db()
    q = request.GET.get('q', '').strip()
    try:
        pagina = int(request.GET.get('page', 1))
    except ValueError:
        pagina = 1
    pagina = max(1, pagina)

    filtro = {}
    if q:
        filtro['nombre'] = {'$regex': re.escape(q), '$options': 'i'}

    total = db.canciones.count_documents(filtro)
    total_paginas = max(1, -(-total // CANCIONES_POR_PAGINA))
    pagina = min(pagina, total_paginas)

    canciones = list(
        db.canciones.find(filtro)
        .sort('nombre', 1)
        .skip((pagina - 1) * CANCIONES_POR_PAGINA)
        .limit(CANCIONES_POR_PAGINA)
    )

    return render(request, 'admin/canciones.html', {
        'canciones': canciones,
        'q': q,
        'pagina': pagina,
        'total_paginas': total_paginas,
        'total': total,
    })


def _generos_desde_texto(texto):
    return [{'nombre': g.strip()} for g in texto.split(',') if g.strip()]


def _generos_a_texto(generos):
    return ', '.join(g.get('nombre', '') for g in generos or [])


@admin_requerido
def cancion_crear(request):
    db = get_db()
    artistas = list(db.artistas.find().sort('nombre', 1))
    form = CancionForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        artista = db.artistas.find_one({'sql_id': form.cleaned_data['artista_sql_id']})
        if not artista:
            form.add_error('artista_sql_id', 'Seleccioná un artista válido.')
        else:
            nuevo_id = siguiente_sql_id(db.canciones)
            db.canciones.insert_one({
                'sql_id': nuevo_id,
                'nombre': form.cleaned_data['nombre'].strip(),
                'estado': form.cleaned_data['estado'],
                'duracion_seg': form.cleaned_data['duracion_seg'],
                'total_reproducciones': 0,
                'generos': _generos_desde_texto(form.cleaned_data['generos_texto']),
                'artista': {'sql_id': artista['sql_id'], 'nombre': artista.get('nombre', '')},
                'album': {
                    'sql_id': 0,
                    'nombre': form.cleaned_data['album_nombre'].strip(),
                    'fecha_lanzamiento': form.cleaned_data['album_fecha'].strip(),
                },
            })
            messages.success(request, 'Canción creada.')
            return redirect('admin_canciones')

    return render(request, 'admin/cancion_form.html', {'form': form, 'artistas': artistas, 'modo': 'crear'})


@admin_requerido
def cancion_editar(request, sql_id):
    db = get_db()
    cancion = db.canciones.find_one({'sql_id': sql_id})
    if not cancion:
        messages.error(request, 'Esa canción no existe.')
        return redirect('admin_canciones')

    artistas = list(db.artistas.find().sort('nombre', 1))
    form = CancionForm(request.POST or None, initial={
        'nombre': cancion.get('nombre', ''),
        'estado': cancion.get('estado', 'Activo'),
        'duracion_seg': cancion.get('duracion_seg', 0),
        'artista_sql_id': cancion.get('artista', {}).get('sql_id'),
        'album_nombre': cancion.get('album', {}).get('nombre', ''),
        'album_fecha': cancion.get('album', {}).get('fecha_lanzamiento', ''),
        'generos_texto': _generos_a_texto(cancion.get('generos')),
    })

    if request.method == 'POST' and form.is_valid():
        artista = db.artistas.find_one({'sql_id': form.cleaned_data['artista_sql_id']})
        if not artista:
            form.add_error('artista_sql_id', 'Seleccioná un artista válido.')
        else:
            db.canciones.update_one({'sql_id': sql_id}, {'$set': {
                'nombre': form.cleaned_data['nombre'].strip(),
                'estado': form.cleaned_data['estado'],
                'duracion_seg': form.cleaned_data['duracion_seg'],
                'generos': _generos_desde_texto(form.cleaned_data['generos_texto']),
                'artista': {'sql_id': artista['sql_id'], 'nombre': artista.get('nombre', '')},
                'album.nombre': form.cleaned_data['album_nombre'].strip(),
                'album.fecha_lanzamiento': form.cleaned_data['album_fecha'].strip(),
            }})
            messages.success(request, 'Canción actualizada.')
            return redirect('admin_canciones')

    return render(request, 'admin/cancion_form.html', {
        'form': form, 'artistas': artistas, 'modo': 'editar', 'cancion': cancion,
    })


@admin_requerido
def cancion_eliminar(request, sql_id):
    if request.method != 'POST':
        return redirect('admin_canciones')
    db = get_db()
    db.canciones.delete_one({'sql_id': sql_id})
    messages.success(request, 'Canción eliminada.')
    return redirect('admin_canciones')


# --------------------------------------------------------------- Artistas

def _parsear_albums(texto):
    """Cada línea: 'Nombre del álbum, AAAA-MM-DD'. La fecha es opcional."""
    albums = []
    for i, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if not linea:
            continue
        partes = linea.rsplit(',', 1)
        nombre = partes[0].strip()
        fecha = partes[1].strip() if len(partes) > 1 else ''
        albums.append({'sql_id': i, 'nombre': nombre, 'fecha_lanzamiento': fecha})
    return albums


def _albums_a_texto(albums):
    lineas = []
    for a in albums or []:
        fecha = a.get('fecha_lanzamiento', '')
        lineas.append(f"{a.get('nombre', '')}, {fecha}" if fecha else a.get('nombre', ''))
    return '\n'.join(lineas)


@admin_requerido
def artistas_lista(request):
    db = get_db()
    artistas = list(db.artistas.find().sort('nombre', 1))
    for a in artistas:
        a['num_albums'] = len(a.get('albums', []))
    return render(request, 'admin/artistas.html', {'artistas': artistas})


@admin_requerido
def artista_crear(request):
    db = get_db()
    form = ArtistaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        nuevo_id = siguiente_sql_id(db.artistas)
        db.artistas.insert_one({
            'sql_id': nuevo_id,
            'nombre': form.cleaned_data['nombre'].strip(),
            'discografia': form.cleaned_data['discografia'].strip(),
            'albums': _parsear_albums(form.cleaned_data['albums_texto']),
        })
        messages.success(request, 'Artista creado.')
        return redirect('admin_artistas')

    return render(request, 'admin/artista_form.html', {'form': form, 'modo': 'crear'})


@admin_requerido
def artista_editar(request, sql_id):
    db = get_db()
    artista = db.artistas.find_one({'sql_id': sql_id})
    if not artista:
        messages.error(request, 'Ese artista no existe.')
        return redirect('admin_artistas')

    form = ArtistaForm(request.POST or None, initial={
        'nombre': artista.get('nombre', ''),
        'discografia': artista.get('discografia', ''),
        'albums_texto': _albums_a_texto(artista.get('albums')),
    })

    if request.method == 'POST' and form.is_valid():
        db.artistas.update_one({'sql_id': sql_id}, {'$set': {
            'nombre': form.cleaned_data['nombre'].strip(),
            'discografia': form.cleaned_data['discografia'].strip(),
            'albums': _parsear_albums(form.cleaned_data['albums_texto']),
        }})
        messages.success(request, 'Artista actualizado.')
        return redirect('admin_artistas')

    return render(request, 'admin/artista_form.html', {'form': form, 'modo': 'editar', 'artista': artista})


@admin_requerido
def artista_eliminar(request, sql_id):
    if request.method != 'POST':
        return redirect('admin_artistas')
    db = get_db()
    db.artistas.delete_one({'sql_id': sql_id})
    messages.success(request, 'Artista eliminado.')
    return redirect('admin_artistas')


# --------------------------------------------------- Playlists / reproducciones (solo lectura)

@admin_requerido
def playlists_lista(request):
    db = get_db()
    playlists = list(db.playlists.find().sort('nombre', 1))
    usuarios_map = {u['sql_id']: u.get('nombre', '') for u in db.usuarios.find()}
    for p in playlists:
        p['num_canciones'] = len(p.get('canciones', []))
        p['creador'] = usuarios_map.get(p.get('usuario_sql_id'), '—')
    return render(request, 'admin/playlists.html', {'playlists': playlists})


@admin_requerido
def reproducciones_lista(request):
    db = get_db()
    reproducciones = list(db.reproducciones.find().sort('fecha', -1))
    usuarios_map = {u['sql_id']: u.get('nombre', '') for u in db.usuarios.find()}
    canciones_map = {c['sql_id']: c.get('nombre', '') for c in db.canciones.find()}
    for r in reproducciones:
        r['usuario_nombre'] = usuarios_map.get(r.get('usuario_sql_id'), '—')
        r['cancion_nombre'] = canciones_map.get(r.get('cancion_sql_id'), '—')
    return render(request, 'admin/reproducciones.html', {'reproducciones': reproducciones})


# --------------------------------------------------------------- Reportes

@admin_requerido
def reportes(request):
    db = get_db()

    # 1. Top canciones más escuchadas, por total_reproducciones.
    top_canciones = list(db.canciones.find().sort('total_reproducciones', -1).limit(10))

    # 2. Oyentes únicos por artista: $lookup entre reproducciones y canciones
    #    (la colección reproducciones no guarda el nombre del artista, así que
    #    lo trae uniéndose con canciones, que sí tiene el artista embebido).
    pipeline_oyentes = [
        {'$lookup': {
            'from': 'canciones',
            'localField': 'cancion_sql_id',
            'foreignField': 'sql_id',
            'as': 'cancion_info',
        }},
        {'$unwind': '$cancion_info'},
        {'$group': {
            '_id': '$cancion_info.artista.sql_id',
            'artista_nombre': {'$first': '$cancion_info.artista.nombre'},
            'oyentes_unicos': {'$addToSet': '$usuario_sql_id'},
        }},
        {'$project': {
            '_id': 0,
            'artista_sql_id': '$_id',
            'artista_nombre': 1,
            'total_oyentes': {'$size': '$oyentes_unicos'},
        }},
        {'$sort': {'total_oyentes': -1}},
    ]
    oyentes_por_artista = list(db.reproducciones.aggregate(pipeline_oyentes))

    # 3. Actividad de playlists: cantidad de canciones por playlist + creador.
    pipeline_playlists = [
        {'$project': {
            '_id': 0,
            'nombre': 1,
            'usuario_sql_id': 1,
            'cantidad_canciones': {'$size': {'$ifNull': ['$canciones', []]}},
        }},
        {'$lookup': {
            'from': 'usuarios',
            'localField': 'usuario_sql_id',
            'foreignField': 'sql_id',
            'as': 'creador_info',
        }},
        {'$sort': {'cantidad_canciones': -1}},
    ]
    actividad_playlists = list(db.playlists.aggregate(pipeline_playlists))
    for p in actividad_playlists:
        info = p.get('creador_info') or [{}]
        p['creador_nombre'] = info[0].get('nombre', '—')

    # 4. Usuarios por tipo (Free/Premium).
    # Los templates de Django no pueden leer "_id" (empieza con guion bajo),
    # por eso se renombra a "tipo" con un $project.
    pipeline_usuarios = [
        {'$group': {'_id': '$tipo', 'cantidad': {'$sum': 1}}},
        {'$project': {'_id': 0, 'tipo': '$_id', 'cantidad': 1}},
        {'$sort': {'tipo': 1}},
    ]
    usuarios_por_tipo = list(db.usuarios.aggregate(pipeline_usuarios))

    return render(request, 'admin/reportes.html', {
        'top_canciones': top_canciones,
        'oyentes_por_artista': oyentes_por_artista,
        'actividad_playlists': actividad_playlists,
        'usuarios_por_tipo': usuarios_por_tipo,
    })
