"""
Formularios de validación (forms.Form, NO ModelForm, porque no hay modelos
de Django: los datos viven en MongoDB y se leen/escriben a mano con PyMongo
en las vistas). Cada form solo valida la forma de los datos que llegan del
usuario; el guardado real ocurre en core/auth.py, views_user.py o views_admin.py.
"""
from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )


class RegistroForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre',
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        label='Contraseña',
        min_length=4,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        return cleaned


class PlaylistForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre de la playlist',
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Para entrenar'}),
    )


class PerfilForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre',
        max_length=120,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )


# ---------- Formularios del panel de admin ----------

class UsuarioForm(forms.Form):
    """Edición de un usuario existente desde el panel de admin."""
    TIPOS = [('Free', 'Free'), ('Premium', 'Premium')]
    ROLES = [('usuario', 'Usuario'), ('admin', 'Admin')]
    ESTADOS_SUSCRIPCION = [('Activa', 'Activa'), ('Cancelada', 'Cancelada'), ('Vencida', 'Vencida')]

    nombre = forms.CharField(label='Nombre', max_length=120, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    tipo = forms.ChoiceField(label='Tipo de cuenta', choices=TIPOS, widget=forms.Select(attrs={'class': 'form-select'}))
    rol = forms.ChoiceField(label='Rol', choices=ROLES, widget=forms.Select(attrs={'class': 'form-select'}))
    suscripcion_estado = forms.ChoiceField(
        label='Estado de suscripción',
        choices=ESTADOS_SUSCRIPCION,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class UsuarioCrearForm(UsuarioForm):
    """Igual que UsuarioForm pero pide una contraseña inicial (solo al crear)."""
    password = forms.CharField(
        label='Contraseña inicial',
        min_length=4,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )


class CancionForm(forms.Form):
    ESTADOS = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]

    nombre = forms.CharField(label='Nombre', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    estado = forms.ChoiceField(label='Estado', choices=ESTADOS, widget=forms.Select(attrs={'class': 'form-select'}))
    duracion_seg = forms.IntegerField(
        label='Duración (segundos)', min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    # Se elige con un <select> armado a mano en el template (a partir de la
    # lista de artistas), por eso no necesita choices acá.
    artista_sql_id = forms.IntegerField(label='Artista')
    album_nombre = forms.CharField(
        label='Álbum', max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    album_fecha = forms.CharField(
        label='Fecha de lanzamiento del álbum', max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AAAA-MM-DD'}),
    )
    generos_texto = forms.CharField(
        label='Géneros (separados por coma)', max_length=300, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pop, Rock'}),
    )


class ArtistaForm(forms.Form):
    nombre = forms.CharField(label='Nombre', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    discografia = forms.CharField(
        label='Discografía / género', max_length=200, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    albums_texto = forms.CharField(
        label='Álbumes (uno por línea: Nombre, AAAA-MM-DD)', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
    )
