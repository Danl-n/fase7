"""Rutas de la app core: diagnóstico, autenticación, usuario y admin."""
from django.urls import path

from core import auth, views, views_admin, views_user

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('ping/', views.ping_mongo, name='ping_mongo'),

    # Autenticación
    path('login/', auth.login_view, name='login'),
    path('logout/', auth.logout_view, name='logout'),
    path('registro/', auth.registro_view, name='registro'),

    # Usuario
    path('dashboard/', views_user.dashboard, name='dashboard'),
    path('explorar/', views_user.explorar, name='explorar'),
    path('cancion/<int:sql_id>/', views_user.detalle_cancion, name='detalle_cancion'),
    path('cancion/<int:sql_id>/like/', views_user.toggle_like, name='toggle_like'),
    path('cancion/<int:sql_id>/reproducir/', views_user.reproducir, name='reproducir'),
    path('artistas/', views_user.artistas, name='artistas'),
    path('artista/<int:sql_id>/seguir/', views_user.toggle_seguir, name='toggle_seguir'),
    path('playlists/', views_user.mis_playlists, name='mis_playlists'),
    path('playlists/<int:sql_id>/', views_user.playlist_detalle, name='playlist_detalle'),
    path('playlists/<int:sql_id>/editar/', views_user.editar_playlist, name='editar_playlist'),
    path('playlists/<int:sql_id>/eliminar/', views_user.eliminar_playlist, name='eliminar_playlist'),
    path('playlists/<int:sql_id>/agregar/', views_user.agregar_cancion_playlist, name='agregar_cancion_playlist'),
    path(
        'playlists/<int:sql_id>/quitar/<int:cancion_sql_id>/',
        views_user.quitar_cancion_playlist,
        name='quitar_cancion_playlist',
    ),
    path('likes/', views_user.mis_likes, name='mis_likes'),
    path('historial/', views_user.mi_historial, name='mi_historial'),
    path('perfil/', views_user.perfil, name='perfil'),

    # Admin
    path('admin/dashboard/', views_admin.dashboard, name='admin_dashboard'),

    path('admin/usuarios/', views_admin.usuarios_lista, name='admin_usuarios'),
    path('admin/usuarios/nuevo/', views_admin.usuario_crear, name='admin_usuario_crear'),
    path('admin/usuarios/<int:sql_id>/editar/', views_admin.usuario_editar, name='admin_usuario_editar'),
    path('admin/usuarios/<int:sql_id>/eliminar/', views_admin.usuario_eliminar, name='admin_usuario_eliminar'),

    path('admin/canciones/', views_admin.canciones_lista, name='admin_canciones'),
    path('admin/canciones/nueva/', views_admin.cancion_crear, name='admin_cancion_crear'),
    path('admin/canciones/<int:sql_id>/editar/', views_admin.cancion_editar, name='admin_cancion_editar'),
    path('admin/canciones/<int:sql_id>/eliminar/', views_admin.cancion_eliminar, name='admin_cancion_eliminar'),

    path('admin/artistas/', views_admin.artistas_lista, name='admin_artistas'),
    path('admin/artistas/nuevo/', views_admin.artista_crear, name='admin_artista_crear'),
    path('admin/artistas/<int:sql_id>/editar/', views_admin.artista_editar, name='admin_artista_editar'),
    path('admin/artistas/<int:sql_id>/eliminar/', views_admin.artista_eliminar, name='admin_artista_eliminar'),

    path('admin/playlists/', views_admin.playlists_lista, name='admin_playlists'),
    path('admin/reproducciones/', views_admin.reproducciones_lista, name='admin_reproducciones'),
    path('admin/reportes/', views_admin.reportes, name='admin_reportes'),
]
