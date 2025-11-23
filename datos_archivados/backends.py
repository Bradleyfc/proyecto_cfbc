from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from .models import UsuarioArchivado
import logging

logger = logging.getLogger(__name__)

class UsuarioArchivadoBackend(BaseBackend):
    """
    Backend de autenticación que permite login con usuarios archivados
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica usuarios tanto de la tabla actual como de datos archivados
        """
        if username is None or password is None:
            return None
        
        # Primero intentar con usuarios actuales (comportamiento normal)
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            pass
        
        # Si no existe en usuarios actuales, buscar en archivados (UsuarioArchivado)
        try:
            usuario_archivado = UsuarioArchivado.objects.get(username=username)
            
            # Verificar si ya tiene un usuario actual vinculado
            if usuario_archivado.usuario_actual:
                user = usuario_archivado.usuario_actual
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            
            # Crear usuario actual basado en datos archivados
            user = self.crear_usuario_desde_archivado(usuario_archivado, password)
            if user:
                # Marcar en la sesión que se creó automáticamente
                if request:
                    request.session['usuario_creado_automaticamente'] = True
                    request.session['usuario_creado_desde'] = 'datos_archivados'
                return user
                
        except UsuarioArchivado.DoesNotExist:
            pass
        
        # Si no existe en UsuarioArchivado, buscar en datos archivados dinámicos (auth_user)
        try:
            from .models import DatoArchivadoDinamico
            
            datos_auth_user = DatoArchivadoDinamico.objects.filter(
                tabla_origen='auth_user',
                datos_originales__username=username
            ).first()
            
            if datos_auth_user:
                datos = datos_auth_user.datos_originales
                password_archivado = datos.get('password', '')
                
                # Verificar contraseña (puede estar en texto plano o hasheada)
                if self.verificar_password_archivado(password, password_archivado):
                    # Crear usuario desde datos archivados dinámicos
                    user = self.crear_usuario_desde_datos_dinamicos(datos_auth_user, password)
                    if user:
                        # Marcar en la sesión que se creó automáticamente
                        if request:
                            request.session['usuario_creado_automaticamente'] = True
                            request.session['usuario_creado_desde'] = 'datos_dinamicos'
                        return user
                        
        except Exception as e:
            logger.error(f"Error buscando en datos archivados dinámicos: {e}")
        
        return None
    
    def crear_usuario_desde_archivado(self, usuario_archivado, password):
        """
        Crea un usuario actual basado en los datos archivados
        """
        try:
            # Generar username único si ya existe
            username_original = usuario_archivado.username
            username_final = self.generar_username_unico(username_original)
            
            # Crear nuevo usuario
            user = User.objects.create_user(
                username=username_final,
                email=usuario_archivado.email,
                first_name=usuario_archivado.first_name,
                last_name=usuario_archivado.last_name,
                password=password,  # Esto hasheará la contraseña
                is_active=usuario_archivado.is_active
            )
            
            # Vincular el usuario archivado con el nuevo usuario
            usuario_archivado.usuario_actual = user
            usuario_archivado.save()
            
            # Asignar siempre al grupo Estudiantes
            try:
                from django.contrib.auth.models import Group
                grupo_estudiantes = Group.objects.get(name='Estudiantes')
                user.groups.add(grupo_estudiantes)
                logger.info(f"Usuario {user.username} agregado al grupo Estudiantes")
            except Group.DoesNotExist:
                logger.warning(f"Grupo 'Estudiantes' no existe. Creando grupo...")
                # Crear el grupo si no existe
                grupo_estudiantes = Group.objects.create(name='Estudiantes')
                user.groups.add(grupo_estudiantes)
                logger.info(f"Grupo 'Estudiantes' creado y usuario {user.username} agregado")
            
            # Enviar email de confirmación
            self.enviar_email_reactivacion(user, username_original, username_final)
            
            logger.info(f"Usuario creado desde datos archivados: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error creando usuario desde archivado: {e}")
            return None
    
    def get_user(self, user_id):
        """
        Obtiene un usuario por su ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def verificar_password_archivado(self, password_ingresado, password_archivado):
        """
        Verifica si la contraseña ingresada coincide con la archivada
        Maneja tanto contraseñas en texto plano como hasheadas
        """
        if not password_archivado:
            return False
        
        # Si la contraseña archivada es texto plano
        if password_archivado == password_ingresado:
            return True
        
        # Si la contraseña archivada está hasheada, usar check_password de Django
        try:
            return check_password(password_ingresado, password_archivado)
        except:
            return False
    
    def crear_usuario_desde_datos_dinamicos(self, dato_archivado, password_ingresado):
        """
        Crea un usuario actual basado en datos archivados dinámicos de auth_user
        Usa la contraseña original de los datos archivados (hasheada o texto plano)
        """
        try:
            datos = dato_archivado.datos_originales
            username_original = datos.get('username', '')
            password_archivado = datos.get('password', '')
            
            if not username_original or not password_archivado:
                return None
            
            # Generar username único si ya existe
            username_final = self.generar_username_unico(username_original)
            
            # Determinar si la contraseña archivada está hasheada o es texto plano
            password_final = self.procesar_password_archivado(password_archivado)
            
            # Crear nuevo usuario usando create() en lugar de create_user() para manejar password manualmente
            user = User(
                username=username_final,
                email=datos.get('email', ''),
                first_name=datos.get('first_name', ''),
                last_name=datos.get('last_name', ''),
                password=password_final,  # Usar contraseña procesada
                is_active=bool(datos.get('is_active', True)),
                is_staff=bool(datos.get('is_staff', False)),
                is_superuser=bool(datos.get('is_superuser', False))
            )
            user.save()
            
            # Asignar siempre al grupo Estudiantes
            try:
                from django.contrib.auth.models import Group
                grupo_estudiantes = Group.objects.get(name='Estudiantes')
                user.groups.add(grupo_estudiantes)
                logger.info(f"Usuario {user.username} agregado al grupo Estudiantes")
            except Group.DoesNotExist:
                logger.warning(f"Grupo 'Estudiantes' no existe. Creando grupo...")
                grupo_estudiantes = Group.objects.create(name='Estudiantes')
                user.groups.add(grupo_estudiantes)
                logger.info(f"Grupo 'Estudiantes' creado y usuario {user.username} agregado")
            
            # Enviar email de confirmación
            self.enviar_email_reactivacion(user, username_original, username_final)
            
            logger.info(f"Usuario creado desde datos archivados dinámicos: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error creando usuario desde datos dinámicos: {e}")
            return None
    
    def procesar_password_archivado(self, password_archivado):
        """
        Procesa la contraseña archivada para determinar si está hasheada o es texto plano
        Retorna la contraseña en el formato correcto para Django
        """
        if not password_archivado:
            return None
        
        # Verificar si la contraseña ya está hasheada (formato Django)
        # Las contraseñas hasheadas de Django tienen el formato: algoritmo$salt$hash
        if '$' in password_archivado and len(password_archivado) > 20:
            # Ya está hasheada, usar tal como está
            logger.info("Contraseña archivada detectada como hasheada")
            return password_archivado
        else:
            # Es texto plano, hashear usando Django
            from django.contrib.auth.hashers import make_password
            password_hasheado = make_password(password_archivado)
            logger.info("Contraseña archivada detectada como texto plano, hasheando...")
            return password_hasheado
    
    def user_can_authenticate(self, user):
        """
        Verifica si el usuario puede autenticarse
        """
        return getattr(user, 'is_active', True)
    
    def generar_username_unico(self, username_base):
        """
        Genera un username único agregando números consecutivos si ya existe
        """
        username_final = username_base
        contador = 0
        
        while User.objects.filter(username=username_final).exists():
            username_final = f"{username_base}{contador}"
            contador += 1
        
        return username_final
    
    def enviar_email_reactivacion(self, user, username_original, username_final):
        """
        Envía email de confirmación cuando se reactiva una cuenta desde datos archivados
        """
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Determinar si el username cambió
            username_cambio = username_original != username_final
            
            # Preparar el mensaje
            if username_cambio:
                mensaje_username = f'''IMPORTANTE: Su nombre de usuario ha cambiado
Nombre de usuario original: {username_original}
Nuevo nombre de usuario: {username_final}

Esto se debe a que ya existía un usuario con el nombre "{username_original}" en el sistema.
Por favor, use "{username_final}" para futuros inicios de sesión.'''
            else:
                mensaje_username = f'Su nombre de usuario es: {username_final}'
            
            # Mensaje completo
            mensaje = f'''¡Bienvenido de vuelta al Centro Fray Bartolomé de las Casas!

Su cuenta ha sido reactivada automáticamente desde los datos archivados.

DETALLES DE SU CUENTA:
{mensaje_username}
Correo electrónico: {user.email}
Nombre completo: {user.get_full_name()}

Ahora puede acceder a todos los servicios del sistema usando sus credenciales.

Si tiene alguna pregunta o necesita ayuda, no dude en contactarnos.

Saludos cordiales,
Centro Fray Bartolomé de las Casas'''
            
            # Enviar email
            send_mail(
                'Cuenta Reactivada - Centro Fray Bartolomé de las Casas',
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            logger.info(f"Email de reactivación enviado a {user.email}")
            
        except Exception as e:
            logger.error(f"Error enviando email de reactivación: {e}")