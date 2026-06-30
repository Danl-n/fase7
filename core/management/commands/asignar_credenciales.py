"""
Comando de gestión: asigna password y rol a los usuarios que ya existían en
la base de datos (cargados antes de tener login). Es idempotente: si un
usuario ya tiene password/rol, no los toca, salvo el usuario designado como
admin, que siempre queda forzado a rol "admin" con su contraseña conocida.

Uso:
    python manage.py asignar_credenciales
"""
from django.core.management.base import BaseCommand
from werkzeug.security import generate_password_hash

from core.db import get_db

PASSWORD_POR_DEFECTO = 'stream123'
ADMIN_EMAIL = 'ana.suarez@email.com'
ADMIN_PASSWORD = 'admin123'


class Command(BaseCommand):
    help = 'Asigna password y rol a los usuarios existentes en MongoDB y designa un admin.'

    def handle(self, *args, **options):
        db = get_db()
        usuarios = db.usuarios

        actualizados = 0
        for u in usuarios.find():
            cambios = {}
            if 'password' not in u:
                cambios['password'] = generate_password_hash(PASSWORD_POR_DEFECTO)
            if 'rol' not in u:
                cambios['rol'] = 'usuario'
            if cambios:
                usuarios.update_one({'_id': u['_id']}, {'$set': cambios})
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f"{actualizados} usuario(s) recibieron password '{PASSWORD_POR_DEFECTO}' "
            f"y/o rol 'usuario' (los que no tenían)."
        ))

        admin_doc = usuarios.find_one({'email': ADMIN_EMAIL})
        if admin_doc:
            usuarios.update_one(
                {'_id': admin_doc['_id']},
                {'$set': {
                    'password': generate_password_hash(ADMIN_PASSWORD),
                    'rol': 'admin',
                }},
            )
            self.stdout.write(self.style.SUCCESS(
                f"Usuario admin configurado: {ADMIN_EMAIL} / contraseña: {ADMIN_PASSWORD}"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"No se encontró ningún usuario con email {ADMIN_EMAIL}. No se asignó admin."
            ))
