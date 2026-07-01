"""
Vistas del rol "usuario": dashboard personal, catálogo de canciones/artistas,
playlists propias, likes, historial de reproducciones y perfil.

Todas estas vistas están protegidas con @login_requerido (core/auth.py) y
acceden a los datos exclusivamente con PyMongo (sin ORM de Django).
"""
import re
from datetime import datetime

from django.contrib import messages
from django.shortcuts import redirect, render

from core.auth import login_requerido
from core.db import get_db
from core.forms import PerfilForm, PlaylistForm
from core.utils import siguiente_sql_id

CANCIONES_POR_PAGINA = 20


def _usuario_actual(request, db):
    """Trae el documento completo del usuario logueado desde Mongo."""
    return db.usuarios.find_one({'sql_id': request.session['user_id']})


def _formatear_duracion(segundos):
    """Convierte segundos a formato m:ss para mostrar en los templates."""
    segundos = segundos or 0
    minutos, seg = divmod(int(segundos), 60)
    return f"{minutos}:{seg:02d}"


@login_requerido
def dashboard(request):
    db = get_db()
    usuario = _usuario_actual(request, db)

    num_playlists = db.playlists.count_documents({'usuario_sql_id': usuario['sql_id']})
    likes = usuario.get('canciones_liked', [])
    seguidos = usuario.get('artistas_seguidos', [])
    suscripcion = usuario.get('suscripcion', {})

    contexto = {
        'usuario': usuario,
        'num_playlists': num_playlists,
        'num_likes': len(likes),
        'num_seguidos': len(seguidos),
        'suscripcion_tipo': suscripcion.get('tipo', usuario.get('tipo', 'Free')),
        'suscripcion_estado': suscripcion.get('estado', 'Sin suscripción'),
    }
    return render(request, 'usuario/dashboard.html', contexto)


@login_requerido
def explorar(request):
    db = get_db()

    q = request.GET.get('q', '').strip()
    genero = request.GET.get('genero', '').strip()
    try:
        pagina = int(request.GET.get('page', 1))
    except ValueError:
        pagina = 1
    pagina = max(1, pagina)

    filtro = {'estado': 'Activo'}
    if q:
        filtro['nombre'] = {'$regex': re.escape(q), '$options': 'i'}
    if genero:
        filtro['generos.nombre'] = genero

    total = db.canciones.count_documents(filtro)
    total_paginas = max(1, -(-total // CANCIONES_POR_PAGINA))  # división hacia arriba
    pagina = min(pagina, total_paginas)

    canciones = list(
        db.canciones.find(filtro)
        .sort('nombre', 1)
        .skip((pagina - 1) * CANCIONES_POR_PAGINA)
        .limit(CANCIONES_POR_PAGINA)
    )
    for c in canciones:
        c['duracion_fmt'] = _formatear_duracion(c.get('duracion_seg'))

    generos_disponibles = sorted(db.canciones.distinct('generos.nombre'))

    contexto = {
        'canciones': canciones,
        'q': q,
        'genero': genero,
        'generos_disponibles': generos_disponibles,
        'pagina': pagina,
        'total_paginas': total_paginas,
        'total': total,
    }
    return render(request, 'usuario/explorar.html', contexto)


@login_requerido
def detalle_cancion(request, sql_id):
    db = get_db()
    cancion = db.canciones.find_one({'sql_id': sql_id})
    if not cancion:
        messages.error(request, 'Esa canción no existe.')
        return redirect('explorar')

    cancion['duracion_fmt'] = _formatear_duracion(cancion.get('duracion_seg'))

    usuario = _usuario_actual(request, db)
    le_gusta = any(c.get('sql_id') == sql_id for c in usuario.get('canciones_liked', []))

    return render(request, 'usuario/detalle_cancion.html', {'cancion': cancion, 'le_gusta': le_gusta})


@login_requerido
def toggle_like(request, sql_id):
    if request.method != 'POST':
        return redirect('detalle_cancion', sql_id=sql_id)

    db = get_db()
    uid = request.session['user_id']
    usuario = db.usuarios.find_one({'sql_id': uid})
    ya_le_gusta = any(c.get('sql_id') == sql_id for c in usuario.get('canciones_liked', []))

    if ya_le_gusta:
        db.usuarios.update_one({'sql_id': uid}, {'$pull': {'canciones_liked': {'sql_id': sql_id}}})
        messages.success(request, 'Quitaste el like.')
    else:
        db.usuarios.update_one({'sql_id': uid}, {'$push': {'canciones_liked': {'sql_id': sql_id}}})
        messages.success(request, '¡Le diste like a la canción!')

    return redirect('detalle_cancion', sql_id=sql_id)


@login_requerido
def reproducir(request, sql_id):
    """
    No reproduce audio real: solo registra el evento en `reproducciones` e
    incrementa `total_reproducciones` de la canción, para demostrar la
    lógica de negocio sin necesitar un archivo de audio.
    """
    if request.method != 'POST':
        return redirect('detalle_cancion', sql_id=sql_id)

    db = get_db()
    cancion = db.canciones.find_one({'sql_id': sql_id})
    if not cancion:
        messages.error(request, 'Esa canción no existe.')
        return redirect('explorar')

    uid = request.session['user_id']
    nuevo_id = siguiente_sql_id(db.reproducciones)
    db.reproducciones.insert_one({
        'sql_id': nuevo_id,
        'usuario_sql_id': uid,
        'cancion_sql_id': sql_id,
        'artista_sql_id': cancion.get('artista', {}).get('sql_id'),
        'fecha': datetime.now().isoformat(),
    })
    db.canciones.update_one({'sql_id': sql_id}, {'$inc': {'total_reproducciones': 1}})

    messages.success(request, f"▶ Reproduciendo \"{cancion.get('nombre', '')}\" (se registró en tu historial).")
    return redirect('detalle_cancion', sql_id=sql_id)


@login_requerido
def artistas(request):
    db = get_db()
    usuario = _usuario_actual(request, db)
    seguidos_ids = {a.get('sql_id') for a in usuario.get('artistas_seguidos', [])}

    lista = list(db.artistas.find().sort('nombre', 1))
    for a in lista:
        a['siguiendo'] = a.get('sql_id') in seguidos_ids

    return render(request, 'usuario/artistas.html', {'artistas': lista})


@login_requerido
def toggle_seguir(request, sql_id):
    if request.method != 'POST':
        return redirect('artistas')

    db = get_db()
    artista = db.artistas.find_one({'sql_id': sql_id})
    if not artista:
        messages.error(request, 'Ese artista no existe.')
        return redirect('artistas')

    uid = request.session['user_id']
    usuario = db.usuarios.find_one({'sql_id': uid})
    ya_sigue = any(a.get('sql_id') == sql_id for a in usuario.get('artistas_seguidos', []))

    if ya_sigue:
        db.usuarios.update_one({'sql_id': uid}, {'$pull': {'artistas_seguidos': {'sql_id': sql_id}}})
        messages.success(request, f"Dejaste de seguir a {artista.get('nombre', '')}.")
    else:
        db.usuarios.update_one(
            {'sql_id': uid},
            {'$push': {'artistas_seguidos': {'sql_id': artista['sql_id'], 'nombre': artista.get('nombre', '')}}},
        )
        messages.success(request, f"Ahora sigues a {artista.get('nombre', '')}.")

    return redirect('artistas')


@login_requerido
def mis_playlists(request):
    db = get_db()
    uid = request.session['user_id']

    form = PlaylistForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        nuevo_id = siguiente_sql_id(db.playlists)
        db.playlists.insert_one({
            'sql_id': nuevo_id,
            'nombre': form.cleaned_data['nombre'].strip(),
            'usuario_sql_id': uid,
            'canciones': [],
        })
        messages.success(request, 'Playlist creada.')
        return redirect('mis_playlists')

    playlists = list(db.playlists.find({'usuario_sql_id': uid}).sort('nombre', 1))
    for p in playlists:
        p['num_canciones'] = len(p.get('canciones', []))

    return render(request, 'usuario/playlists.html', {'playlists': playlists, 'form': form})


def _playlist_del_usuario_o_404(db, request, sql_id):
    """Trae una playlist verificando que sea del usuario logueado (evita que
    un usuario edite/borre playlists ajenas)."""
    playlist = db.playlists.find_one({'sql_id': sql_id, 'usuario_sql_id': request.session['user_id']})
    if not playlist:
        return None
    return playlist


@login_requerido
def playlist_detalle(request, sql_id):
    db = get_db()
    playlist = _playlist_del_usuario_o_404(db, request, sql_id)
    if not playlist:
        messages.error(request, 'Esa playlist no existe o no te pertenece.')
        return redirect('mis_playlists')

    q = request.GET.get('q', '').strip()
    resultados_busqueda = []
    if q:
        ids_en_playlist = {c.get('sql_id') for c in playlist.get('canciones', [])}
        encontradas = db.canciones.find({
            'nombre': {'$regex': re.escape(q), '$options': 'i'},
            'estado': 'Activo',
        }).limit(10)
        resultados_busqueda = [c for c in encontradas if c.get('sql_id') not in ids_en_playlist]

    return render(request, 'usuario/playlist_detalle.html', {
        'playlist': playlist,
        'q': q,
        'resultados_busqueda': resultados_busqueda,
    })


@login_requerido
def agregar_cancion_playlist(request, sql_id):
    if request.method != 'POST':
        return redirect('playlist_detalle', sql_id=sql_id)

    db = get_db()
    playlist = _playlist_del_usuario_o_404(db, request, sql_id)
    if not playlist:
        messages.error(request, 'Esa playlist no existe o no te pertenece.')
        return redirect('mis_playlists')

    try:
        cancion_sql_id = int(request.POST.get('cancion_sql_id'))
    except (TypeError, ValueError):
        messages.error(request, 'Canción inválida.')
        return redirect('playlist_detalle', sql_id=sql_id)

    cancion = db.canciones.find_one({'sql_id': cancion_sql_id})
    if not cancion:
        messages.error(request, 'Esa canción no existe.')
        return redirect('playlist_detalle', sql_id=sql_id)

    ya_esta = any(c.get('sql_id') == cancion_sql_id for c in playlist.get('canciones', []))
    if ya_esta:
        messages.warning(request, 'Esa canción ya está en la playlist.')
    else:
        db.playlists.update_one(
            {'sql_id': sql_id},
            {'$push': {'canciones': {
                'sql_id': cancion['sql_id'],
                'nombre': cancion.get('nombre', ''),
                'artista': cancion.get('artista', {}).get('nombre', ''),
            }}},
        )
        messages.success(request, f"\"{cancion.get('nombre', '')}\" agregada a la playlist.")

    return redirect('playlist_detalle', sql_id=sql_id)


@login_requerido
def quitar_cancion_playlist(request, sql_id, cancion_sql_id):
    if request.method != 'POST':
        return redirect('playlist_detalle', sql_id=sql_id)

    db = get_db()
    playlist = _playlist_del_usuario_o_404(db, request, sql_id)
    if not playlist:
        messages.error(request, 'Esa playlist no existe o no te pertenece.')
        return redirect('mis_playlists')

    db.playlists.update_one({'sql_id': sql_id}, {'$pull': {'canciones': {'sql_id': cancion_sql_id}}})
    messages.success(request, 'Canción quitada de la playlist.')
    return redirect('playlist_detalle', sql_id=sql_id)


@login_requerido
def editar_playlist(request, sql_id):
    db = get_db()
    playlist = _playlist_del_usuario_o_404(db, request, sql_id)
    if not playlist:
        messages.error(request, 'Esa playlist no existe o no te pertenece.')
        return redirect('mis_playlists')

    form = PlaylistForm(request.POST or None, initial={'nombre': playlist.get('nombre', '')})
    if request.method == 'POST' and form.is_valid():
        db.playlists.update_one({'sql_id': sql_id}, {'$set': {'nombre': form.cleaned_data['nombre'].strip()}})
        messages.success(request, 'Playlist actualizada.')
        return redirect('mis_playlists')

    return render(request, 'usuario/playlist_form.html', {'form': form, 'playlist': playlist})


@login_requerido
def eliminar_playlist(request, sql_id):
    if request.method != 'POST':
        return redirect('mis_playlists')

    db = get_db()
    playlist = _playlist_del_usuario_o_404(db, request, sql_id)
    if not playlist:
        messages.error(request, 'Esa playlist no existe o no te pertenece.')
        return redirect('mis_playlists')

    db.playlists.delete_one({'sql_id': sql_id})
    messages.success(request, 'Playlist eliminada.')
    return redirect('mis_playlists')


@login_requerido
def mis_likes(request):
    db = get_db()
    usuario = _usuario_actual(request, db)
    ids_liked = [c.get('sql_id') for c in usuario.get('canciones_liked', [])]

    canciones = []
    if ids_liked:
        canciones = list(db.canciones.find({'sql_id': {'$in': ids_liked}}).sort('nombre', 1))
        for c in canciones:
            c['duracion_fmt'] = _formatear_duracion(c.get('duracion_seg'))

    return render(request, 'usuario/likes.html', {'canciones': canciones})


@login_requerido
def mi_historial(request):
    db = get_db()
    uid = request.session['user_id']

    reproducciones = list(db.reproducciones.find({'usuario_sql_id': uid}).sort('fecha', -1))

    ids_canciones = {r.get('cancion_sql_id') for r in reproducciones if r.get('cancion_sql_id') is not None}
    canciones_map = {}
    if ids_canciones:
        for c in db.canciones.find({'sql_id': {'$in': list(ids_canciones)}}):
            canciones_map[c['sql_id']] = c

    for r in reproducciones:
        r['cancion'] = canciones_map.get(r.get('cancion_sql_id'), {})

    return render(request, 'usuario/historial.html', {'reproducciones': reproducciones})


@login_requerido
def perfil(request):
    db = get_db()
    uid = request.session['user_id']
    usuario = db.usuarios.find_one({'sql_id': uid})

    form = PerfilForm(request.POST or None, initial={
        'nombre': usuario.get('nombre', ''),
        'email': usuario.get('email', ''),
    })

    if request.method == 'POST' and form.is_valid():
        nuevo_email = form.cleaned_data['email'].strip().lower()
        otro_con_ese_email = db.usuarios.find_one({'email': nuevo_email, 'sql_id': {'$ne': uid}})
        if otro_con_ese_email:
            form.add_error('email', 'Ya hay otra cuenta con ese email.')
        else:
            db.usuarios.update_one({'sql_id': uid}, {'$set': {
                'nombre': form.cleaned_data['nombre'].strip(),
                'email': nuevo_email,
            }})
            request.session['user_nombre'] = form.cleaned_data['nombre'].strip()
            request.session['user_email'] = nuevo_email
            messages.success(request, 'Perfil actualizado.')
            return redirect('perfil')

    return render(request, 'usuario/perfil.html', {'form': form, 'usuario': usuario})
