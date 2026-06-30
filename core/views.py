"""
Vistas de diagnóstico / utilidad general que no pertenecen ni al flujo de
usuario final ni al de admin (por ejemplo, la página de prueba de conexión).
"""
from django.http import HttpResponse
from django.shortcuts import redirect

from core.db import get_db


def ping_mongo(request):
    """
    Vista de prueba del Bloque (a): confirma que la conexión a MongoDB Atlas
    funciona, mostrando 5 canciones reales de la colección `canciones`.
    Se puede borrar (o dejar como health-check) una vez verificada la conexión.
    """
    db = get_db()
    canciones = list(db.canciones.find().limit(5))

    filas = ''.join(
        f"<li>{c.get('nombre', '(sin nombre)')} — "
        f"{c.get('artista', {}).get('nombre', '(sin artista)')}</li>"
        for c in canciones
    )

    total_canciones = db.canciones.count_documents({})

    html = f"""
    <h1>StreamMusic — Prueba de conexión a MongoDB Atlas</h1>
    <p>Conexión OK. Total de documentos en 'canciones': {total_canciones}</p>
    <p>Primeras 5 canciones:</p>
    <ul>{filas}</ul>
    """
    return HttpResponse(html)


def inicio(request):
    """Landing post-login: redirige al dashboard correspondiente según el rol."""
    if not request.session.get('user_id'):
        return redirect('login')

    if request.session.get('user_rol') == 'admin':
        return redirect('admin_dashboard')

    return redirect('dashboard')
