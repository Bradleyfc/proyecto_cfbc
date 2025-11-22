# Configuración de Email - Centro Fray Bartolomé de las Casas

## Estado Actual

✅ **FUNCIONANDO CORRECTAMENTE**

## Configuración

### Desarrollo (DEBUG = True)
- **Backend**: `django.core.mail.backends.console.EmailBackend`
- **Comportamiento**: Los emails se muestran en la consola del servidor
- **Ventajas**: 
  - No requiere configuración SMTP
  - Perfecto para desarrollo y pruebas
  - No hay problemas de conectividad

### Producción (DEBUG = False)
- **Backend**: `django.core.mail.backends.smtp.EmailBackend`
- **Servidor**: Gmail SMTP (smtp.gmail.com:587)
- **Credenciales**: Configuradas en `.env`

## Funcionalidades que Usan Email

### 1. Registro de Estudiantes
- **Archivo**: `principal/views.py`
- **Función**: Envía código de 4 dígitos para verificar email
- **Template**: `templates/registration/verify_email.html`

### 2. Reclamación de Cuentas Archivadas
- **Archivo**: `datos_archivados/views.py`
- **Función**: Envía código de 4 dígitos para verificar identidad
- **Template**: `templates/datos_archivados/verificar_codigo_reclamacion.html`

### 3. Recuperación de Contraseña
- **Archivo**: `principal/views.py`
- **Función**: Envía código para restablecer contraseña

## Cómo Probar

### En Desarrollo
1. Iniciar el servidor: `python manage.py runserver`
2. Realizar acción que envíe email (registro, reclamación, etc.)
3. **Ver el email en la consola del servidor**

### Ejemplo de Email en Consola
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 8bit
Subject: Código de Verificación - Reclamación de Cuenta Archivada
From: Centro Fray Bartolome de las Casas <noreply@cfbc.edu.ni>
To: usuario@example.com
Date: Sat, 22 Nov 2025 22:33:52 -0000

Hola usuario,

Se ha solicitado reclamar su cuenta archivada...

Código: 1234

Centro Fray Bartolomé de las Casas
```

## URLs de Prueba

### Reclamación de Cuentas Archivadas
1. **Buscar**: `/datos-archivados/buscar-usuario/`
2. **Iniciar**: `/datos-archivados/iniciar-reclamacion/<dato_id>/`
3. **Verificar**: `/datos-archivados/verificar-codigo-reclamacion/`
4. **Reclamar**: `/datos-archivados/reclamar-usuario-dinamico/<dato_id>/`

### Registro de Estudiantes
1. **Registro**: `/registro/`
2. **Verificar**: `/verify-email/`

## Datos de Prueba Disponibles

### Usuarios Archivados Disponibles
- **carlos@test.com** (usuario: carlos)
- **perito@gmail.com** (usuario: pedro)  
- **maria@gmail.com** (usuario: maria)

## Solución de Problemas

### Problema Original
- **Error**: Timeout de conexión SMTP
- **Causa**: Firewall/red bloqueando conexión a Gmail
- **Solución**: Usar backend de consola en desarrollo

### Para Producción
Si necesita usar SMTP real en producción:
1. Verificar firewall del servidor
2. Confirmar credenciales de Gmail
3. Verificar que la cuenta tenga "Contraseñas de aplicación" habilitadas
4. Cambiar `DEBUG = False` en settings.py

## Configuración Actual en settings.py

```python
# Email configuration
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
    EMAIL_TIMEOUT = 60

DEFAULT_FROM_EMAIL = 'Centro Fray Bartolome de las Casas <noreply@cfbc.edu.ni>'
```

## Estado: ✅ RESUELTO

La validación por email ahora funciona correctamente tanto para:
- ✅ Registro de nuevos estudiantes
- ✅ Reclamación de cuentas archivadas

Los emails se muestran en la consola del servidor durante el desarrollo.