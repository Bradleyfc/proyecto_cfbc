# 🔐 SISTEMA DE RECUPERACIÓN DE USUARIOS ARCHIVADOS

## 📋 Descripción General

Este sistema permite que usuarios archivados de la base de datos antigua (MariaDB) puedan recuperar su acceso al sistema de tres formas diferentes. **Todos los usuarios recuperados son automáticamente asignados al grupo "Estudiantes"**.

---

## 🎯 Las Tres Opciones de Recuperación

### 1️⃣ Backend de Autenticación Automático (Principal)

**Estado:** ✅ ACTIVO

**¿Cómo funciona?**
- El usuario intenta hacer login normalmente en la página de inicio de sesión
- Si el usuario no existe en la base de datos actual, el sistema busca automáticamente en los datos archivados
- Si encuentra el usuario y la contraseña coincide, crea automáticamente una cuenta nueva
- El usuario es redirigido a su perfil sin darse cuenta de que su cuenta fue migrada

**Ventajas:**
- ✅ Completamente transparente para el usuario
- ✅ No requiere pasos adicionales
- ✅ Usa la contraseña original del usuario
- ✅ Automáticamente asignado al grupo "Estudiantes"

**Flujo:**
```
Usuario → Ingresa username/password → Sistema busca en archivados → 
Crea cuenta automáticamente → Login exitoso → Asignado a "Estudiantes"
```

**Ubicación del código:** `datos_archivados/backends.py`

**Configuración en settings.py:**
```python
AUTHENTICATION_BACKENDS = [
    'datos_archivados.backends.UsuarioArchivadoBackend',  # Backend personalizado
    'django.contrib.auth.backends.ModelBackend',          # Backend por defecto
]
```

---

### 2️⃣ Sistema de Reclamación Manual (Alternativo)

**Estado:** ✅ ACTIVO

**¿Cómo funciona?**
- El usuario hace clic en "¿Olvidaste tu contraseña?" o "Recuperar cuenta" en el login
- Busca su usuario archivado por username o email
- Ingresa su contraseña antigua para verificar identidad
- Elige una nueva contraseña
- El sistema crea su cuenta y lo loguea automáticamente

**Ventajas:**
- ✅ El usuario tiene control total del proceso
- ✅ Puede elegir una nueva contraseña
- ✅ Verifica identidad con contraseña antigua
- ✅ Automáticamente asignado al grupo "Estudiantes"

**Flujo:**
```
Usuario → "Recuperar cuenta" → Busca su username → 
Ingresa contraseña antigua → Elige nueva contraseña → 
Cuenta creada → Login automático → Asignado a "Estudiantes"
```

**URLs disponibles:**
- `/datos-archivados/reclamar-usuario/` - Formulario de reclamación
- `/datos-archivados/buscar-usuario/` - Búsqueda de usuarios archivados

**Ubicación del código:** 
- Vista: `datos_archivados/views.py` → `reclamar_usuario_archivado()`
- Formulario: `datos_archivados/forms.py` → `ReclamarUsuarioArchivadoForm`
- Template: `templates/datos_archivados/reclamar_usuario.html`

---

### 3️⃣ Comando Administrativo (Para Administradores)

**Estado:** ✅ ACTIVO

**¿Cómo funciona?**
- El administrador ejecuta un comando de Django desde la terminal
- El sistema migra todos los usuarios archivados de una vez
- Asigna una contraseña temporal a todos
- Los usuarios pueden cambiar su contraseña después del primer login

**Ventajas:**
- ✅ Migración masiva de muchos usuarios a la vez
- ✅ Útil para migrar toda una base de datos
- ✅ Permite simulación antes de aplicar cambios
- ✅ Todos asignados automáticamente al grupo "Estudiantes"

**Comando básico:**
```bash
python manage.py migrar_usuarios_archivados
```

**Opciones disponibles:**

```bash
# Migración normal con contraseña por defecto
python manage.py migrar_usuarios_archivados

# Especificar contraseña temporal personalizada
python manage.py migrar_usuarios_archivados --password-default "MiPassword123"

# Modo simulación (no hace cambios reales)
python manage.py migrar_usuarios_archivados --dry-run

# Forzar migración incluso si el usuario ya existe
python manage.py migrar_usuarios_archivados --force
```

**Flujo:**
```
Administrador → Ejecuta comando → Sistema migra todos los usuarios → 
Asigna contraseña temporal → Vincula con datos archivados → 
Todos asignados a "Estudiantes"
```

**Ubicación del código:** `datos_archivados/management/commands/migrar_usuarios_archivados.py`

---

## 👥 Asignación Automática al Grupo "Estudiantes"

### ¿Qué es el grupo "Estudiantes"?

Es un grupo de Django que permite gestionar permisos de forma centralizada. Todos los usuarios recuperados son automáticamente asignados a este grupo.

### ¿Cuándo se asigna?

En **todas las opciones** de recuperación:
1. ✅ Backend automático → Asigna al crear el usuario
2. ✅ Reclamación manual → Asigna al crear el usuario
3. ✅ Comando administrativo → Asigna al migrar el usuario

### ¿Qué pasa si el grupo no existe?

El sistema lo crea automáticamente. No requiere configuración previa.

### Código de asignación:

```python
# Se ejecuta en las tres opciones
try:
    grupo_estudiantes = Group.objects.get(name='Estudiantes')
    user.groups.add(grupo_estudiantes)
except Group.DoesNotExist:
    # Crear el grupo si no existe
    grupo_estudiantes = Group.objects.create(name='Estudiantes')
    user.groups.add(grupo_estudiantes)
```

---

## 🔄 Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO INTENTA LOGIN                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          ¿Existe en base de datos actual?                    │
└─────────────────────────────────────────────────────────────┘
            │                                   │
           SÍ                                  NO
            │                                   │
            ▼                                   ▼
    ┌──────────────┐              ┌──────────────────────────┐
    │ Login normal │              │ Backend busca archivados │
    └──────────────┘              └──────────────────────────┘
                                              │
                                              ▼
                                  ┌──────────────────────────┐
                                  │ ¿Encontrado en archivos? │
                                  └──────────────────────────┘
                                      │              │
                                     SÍ             NO
                                      │              │
                                      ▼              ▼
                        ┌──────────────────┐  ┌──────────────┐
                        │ Crea usuario     │  │ Login falla  │
                        │ Asigna grupo     │  │              │
                        │ "Estudiantes"    │  │ Opción:      │
                        │ Login exitoso    │  │ "Recuperar   │
                        └──────────────────┘  │  cuenta"     │
                                              └──────────────┘
                                                      │
                                                      ▼
                                          ┌──────────────────────┐
                                          │ Reclamación manual   │
                                          │ Asigna "Estudiantes" │
                                          └──────────────────────┘
```

---

## 📊 Comparación de las Tres Opciones

| Característica | Backend Automático | Reclamación Manual | Comando Admin |
|----------------|-------------------|-------------------|---------------|
| **Transparencia** | ✅ Total | ⚠️ Requiere acción | ⚠️ Requiere admin |
| **Control usuario** | ❌ Ninguno | ✅ Total | ❌ Ninguno |
| **Nueva contraseña** | ❌ Usa la antigua | ✅ Elige nueva | ⚠️ Temporal |
| **Velocidad** | ⚡ Instantáneo | ⏱️ 2-3 minutos | ⚡ Masivo |
| **Grupo Estudiantes** | ✅ Automático | ✅ Automático | ✅ Automático |
| **Requiere admin** | ❌ No | ❌ No | ✅ Sí |
| **Migración masiva** | ❌ Uno por uno | ❌ Uno por uno | ✅ Todos a la vez |

---

## 🛠️ Configuración Requerida

### 1. Backend en settings.py

```python
AUTHENTICATION_BACKENDS = [
    'datos_archivados.backends.UsuarioArchivadoBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### 2. URLs en urls.py principal

```python
urlpatterns = [
    # ... otras URLs
    path('datos-archivados/', include('datos_archivados.urls')),
]
```

### 3. Grupo "Estudiantes"

No requiere configuración. Se crea automáticamente si no existe.

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Usuario recupera cuenta automáticamente

```
1. Usuario va a: http://tudominio.com/login/
2. Ingresa: username="juan", password="mipassword123"
3. Sistema busca en archivados
4. Crea cuenta automáticamente
5. Asigna al grupo "Estudiantes"
6. Usuario ve su perfil sin darse cuenta de la migración
```

### Ejemplo 2: Usuario reclama cuenta manualmente

```
1. Usuario va a: http://tudominio.com/datos-archivados/reclamar-usuario/
2. Busca su username: "maria"
3. Ingresa contraseña antigua: "oldpass"
4. Elige nueva contraseña: "newpass123"
5. Sistema crea cuenta
6. Asigna al grupo "Estudiantes"
7. Login automático
```

### Ejemplo 3: Admin migra todos los usuarios

```bash
# Terminal del servidor
$ python manage.py migrar_usuarios_archivados --password-default "Temporal2024"

Usuarios archivados a procesar: 150
✓ Migrado: juan -> juan
✓ Usuario juan agregado al grupo Estudiantes
✓ Migrado: maria -> maria
✓ Usuario maria agregado al grupo Estudiantes
...
RESUMEN:
Total procesados: 150
Migrados exitosamente: 148
Ya existían: 2
Errores: 0
```

---

## 🔒 Seguridad

### Verificación de contraseñas

- ✅ Las contraseñas archivadas pueden estar hasheadas o en texto plano
- ✅ El sistema detecta automáticamente el formato
- ✅ Siempre hashea las contraseñas antes de guardar en la base actual

### Protección de datos

- ✅ Solo usuarios con permisos pueden ver datos archivados
- ✅ Las contraseñas nunca se muestran en la interfaz
- ✅ Los logs registran todas las migraciones

---

## 📈 Monitoreo

### Ver usuarios migrados

```python
from django.contrib.auth.models import User, Group

# Ver todos los usuarios del grupo Estudiantes
grupo = Group.objects.get(name='Estudiantes')
estudiantes = grupo.user_set.all()
print(f"Total estudiantes: {estudiantes.count()}")
```

### Ver usuarios pendientes de migrar

```python
from datos_archivados.models import UsuarioArchivado

# Usuarios archivados sin cuenta actual
pendientes = UsuarioArchivado.objects.filter(usuario_actual__isnull=True)
print(f"Usuarios pendientes: {pendientes.count()}")
```

---

## ❓ Preguntas Frecuentes

### ¿Qué pasa si un usuario ya existe?

El backend automático no lo sobrescribe. El comando admin puede forzar actualización con `--force`.

### ¿Puedo cambiar el grupo asignado?

Sí, modifica el código en `backends.py` y `migrar_usuarios_archivados.py` para cambiar `'Estudiantes'` por otro grupo.

### ¿Los usuarios pueden cambiar su contraseña después?

Sí, pueden usar la función normal de "Cambiar contraseña" de Django.

### ¿Qué pasa si el grupo "Estudiantes" no existe?

Se crea automáticamente. No requiere configuración previa.

---

## 📞 Soporte

Para problemas o dudas:
1. Revisa los logs en `logs/django.log`
2. Verifica que el backend esté configurado en `settings.py`
3. Asegúrate de que los datos archivados existan en la base de datos

---

**✅ Sistema completamente funcional y probado**

Todas las opciones están activas y funcionando correctamente. Los usuarios pueden recuperar su acceso de la forma que prefieran, y todos serán automáticamente asignados al grupo "Estudiantes".
