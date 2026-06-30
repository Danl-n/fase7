"""
URLs raíz del proyecto. Todo se delega a core.urls, que contiene las rutas
de autenticación, vistas de usuario y vistas de admin.
"""
from django.urls import path, include

urlpatterns = [
    path('', include('core.urls')),
]
