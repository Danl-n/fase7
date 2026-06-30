"""
Conexión a MongoDB Atlas vía PyMongo.

Patrón singleton: como Python solo ejecuta el cuerpo de un módulo la primera
vez que se importa (las importaciones siguientes reutilizan el mismo objeto
en memoria), basta con crear el MongoClient una sola vez aquí, a nivel de
módulo. Todas las vistas que hagan `from core.db import get_db` van a
compartir la misma conexión/pool, en vez de abrir una conexión nueva por request.
"""
from django.conf import settings
from pymongo import MongoClient

_cliente = None
_db = None


def get_db():
    """Devuelve el objeto Database de PyMongo, creando la conexión si hace falta."""
    global _cliente, _db

    if _db is not None:
        return _db

    if not settings.MONGO_URI:
        raise RuntimeError(
            "No se encontró MONGO_URI. Copia .env.example a .env y completa "
            "tu cadena de conexión de MongoDB Atlas."
        )

    _cliente = MongoClient(settings.MONGO_URI)
    _db = _cliente[settings.MONGO_DB]
    return _db
