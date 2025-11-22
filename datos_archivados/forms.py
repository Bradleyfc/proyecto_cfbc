from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioArchivado

class ReclamarUsuarioArchivadoForm(forms.Form):
    """
    Formulario para que usuarios reclamen su cuenta archivada
    """
    username = forms.CharField(
        max_length=150,
        label='Nombre de usuario',
        help_text='Ingrese su nombre de usuario anterior'
    )
    email = forms.EmailField(
        label='Correo electrónico',
        help_text='Ingrese el correo asociado a su cuenta anterior'
    )
    carnet = forms.CharField(
        max_length=11,
        required=False,
        label='Carnet de identidad',
        help_text='Ingrese su carnet para verificar identidad (opcional)'
    )
    nueva_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Nueva contraseña',
        min_length=8
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirmar contraseña'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        carnet = cleaned_data.get('carnet')
        nueva_password = cleaned_data.get('nueva_password')
        confirmar_password = cleaned_data.get('confirmar_password')
        
        # Verificar que las contraseñas coincidan
        if nueva_password and confirmar_password:
            if nueva_password != confirmar_password:
                raise forms.ValidationError('Las contraseñas no coinciden')
        
        # Verificar que el usuario archivado existe
        if username and email:
            try:
                usuario_archivado = UsuarioArchivado.objects.get(
                    username=username,
                    email=email
                )
                
                # Verificar carnet si se proporciona
                if carnet and usuario_archivado.carnet:
                    if usuario_archivado.carnet != carnet:
                        raise forms.ValidationError('Los datos no coinciden con los registros')
                
                # Verificar que no tenga ya un usuario actual
                if usuario_archivado.usuario_actual:
                    raise forms.ValidationError(
                        'Esta cuenta ya ha sido reclamada. Intente recuperar su contraseña.'
                    )
                
                # Verificar que no exista ya un usuario con ese username
                if User.objects.filter(username=username).exists():
                    raise forms.ValidationError(
                        'Ya existe un usuario con ese nombre. Contacte al administrador.'
                    )
                
                cleaned_data['usuario_archivado'] = usuario_archivado
                
            except UsuarioArchivado.DoesNotExist:
                raise forms.ValidationError(
                    'No se encontró un usuario archivado con esos datos'
                )
        
        return cleaned_data
    
    def save(self):
        """
        Crea el usuario actual basado en los datos archivados
        """
        usuario_archivado = self.cleaned_data['usuario_archivado']
        nueva_password = self.cleaned_data['nueva_password']
        
        # Crear usuario actual
        user = User.objects.create_user(
            username=usuario_archivado.username,
            email=usuario_archivado.email,
            first_name=usuario_archivado.first_name,
            last_name=usuario_archivado.last_name,
            password=nueva_password,
            is_active=True
        )
        
        # Asignar siempre al grupo Estudiantes
        try:
            from django.contrib.auth.models import Group
            grupo_estudiantes = Group.objects.get(name='Estudiantes')
            user.groups.add(grupo_estudiantes)
        except Group.DoesNotExist:
            # Crear el grupo si no existe
            grupo_estudiantes = Group.objects.create(name='Estudiantes')
            user.groups.add(grupo_estudiantes)
        
        # Vincular usuario archivado con usuario actual
        usuario_archivado.usuario_actual = user
        usuario_archivado.save()
        
        return user

class BuscarUsuarioArchivadoForm(forms.Form):
    """
    Formulario para buscar usuarios archivados
    """
    busqueda = forms.CharField(
        max_length=200,
        label='Buscar usuario',
        help_text='Ingrese nombre de usuario, email o nombre completo',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: juan.perez, juan@email.com, Juan Pérez',
            'class': 'form-control'
        })
    )
    
    def buscar_usuarios(self):
        """
        Busca usuarios archivados basado en el término de búsqueda
        """
        busqueda = self.cleaned_data.get('busqueda', '').strip()
        
        if not busqueda:
            return UsuarioArchivado.objects.none()
        
        # Buscar por username, email, nombre o apellido
        from django.db.models import Q
        
        return UsuarioArchivado.objects.filter(
            Q(username__icontains=busqueda) |
            Q(email__icontains=busqueda) |
            Q(first_name__icontains=busqueda) |
            Q(last_name__icontains=busqueda) |
            Q(carnet__icontains=busqueda)
        ).order_by('username')