# Sistema de Reclamación de Cuentas Archivadas - Resumen Final

## 📋 Descripción General

Sistema completo para que usuarios recuperen sus cuentas archivadas del sistema anterior con verificación por email mediante códigos de 4 dígitos.

---

## 🔄 Métodos de Reclamación Implementados

### Método 1: Login Automático
- **URL**: `/login/`
- **Funcionamiento**: Usuario ingresa credenciales archivadas → Sistema crea cuenta automáticamente
- **Verificación**: No requiere (usa contraseña original)
- **Backend**: `datos_archivados.backends.UsuarioArchivadoBackend`

### Método 2: Búsqueda por Email
- **URL**: `/datos-archivados/buscar-usuario/`
- **Funcionamiento**: Usuario busca por email → Selecciona cuenta → Verifica código → Establece contraseña
- **Verificación**: Código de 4 dígitos por email
- **Flujo**: Búsqueda → Código → Nueva contraseña → Cuenta creada

### Método 3: Formulario Tradicional
- **URL**: `/datos-archivados/reclamar-usuario/`
- **Funcionamiento**: Usuario completa formulario → Verifica código → Cuenta reactivada
- **Verificación**: Código de 4 dígitos por email
- **Flujo**: Formulario → Código → Cuenta creada automáticamente

---

## 🔐 Sistema de Verificación

### Códigos de 4 Dígitos
- **Generación**: Aleatoria (0000-9999)
- **Expiración**: 15 minutos
- **Uso**: Único (se marca como usado después de validar)
- **Reenvío**: Disponible con invalidación de códigos anteriores

### Modelo: CodigoVerificacionReclamacion
- `email`: Email del usuario
- `codigo`: Código de 4 dígitos
- `fecha_creacion`: Timestamp de creación
- `fecha_expiracion`: Timestamp de expiración
- `usado`: Boolean
- `usuario_archivado`: FK a UsuarioArchivado (nullable)
- `dato_archivado`: FK a DatoArchivadoDinamico (nullable)

---

## 👤 Generación de Usernames Únicos

### Algoritmo
```
username_base = "maria"

Si "maria" existe:
  Probar "maria0"
Si "maria0" existe:
  Probar "maria1"
...
Hasta encontrar uno disponible
```

### Protección contra Race Conditions
- Usa try-except con IntegrityError
- Si falla al crear, intenta con el siguiente número
- Máximo 100 intentos

---

## 📧 Sistema de Emails

### Configuración
- **Desarrollo**: Backend de consola (emails en terminal)
- **Producción**: SMTP de Gmail (configurar en `.env`)

### Tipos de Emails

**1. Código de Verificación**
```
Subject: Código de Verificación - Reclamación de Cuenta Archivada
Contenido: Código de 4 dígitos + Expiración
```

**2. Confirmación de Reactivación**
```
Subject: Cuenta Reactivada - Centro Fray Bartolomé de las Casas
Contenido: Detalles de cuenta + Notificación de cambio de username (si aplica)
```

**3. Reenvío de Código**
```
Subject: Nuevo Código de Verificación - Reclamación de Cuenta
Contenido: Nuevo código de 4 dígitos
```

---

## 🗄️ Fuentes de Datos

### UsuarioArchivado
Usuarios migrados del sistema anterior con estructura completa.

### DatoArchivadoDinamico
Datos de cualquier tabla archivada (incluyendo auth_user).

### Búsqueda Dual
El sistema busca en ambas fuentes automáticamente.

---

## 🎯 Características Principales

- ✅ Verificación por email con código de 4 dígitos
- ✅ Generación automática de usernames únicos
- ✅ Protección contra race conditions
- ✅ Reenvío de códigos
- ✅ Emails de confirmación
- ✅ Login automático después de reactivar
- ✅ Búsqueda en múltiples fuentes de datos
- ✅ Interfaz intuitiva y consistente
- ✅ Mensajes claros y descriptivos

---

## 📁 Archivos Principales

### Backend
- `datos_archivados/backends.py` - Backend de autenticación personalizado
- `datos_archivados/models.py` - Modelos de datos archivados
- `datos_archivados/views.py` - Vistas de reclamación
- `datos_archivados/forms.py` - Formularios de búsqueda y reclamación
- `datos_archivados/urls.py` - URLs del sistema

### Templates
- `templates/datos_archivados/buscar_usuario.html`
- `templates/datos_archivados/reclamar_usuario.html`
- `templates/datos_archivados/verificar_codigo_reclamacion.html`
- `templates/datos_archivados/verificar_codigo_reclamacion_tradicional.html`
- `templates/datos_archivados/reclamar_usuario_dinamico.html`

---

## 🚀 URLs Disponibles

```
/datos-archivados/buscar-usuario/
/datos-archivados/reclamar-usuario/
/datos-archivados/iniciar-reclamacion/<dato_id>/
/datos-archivados/verificar-codigo-reclamacion/
/datos-archivados/verificar-codigo-reclamacion-tradicional/
/datos-archivados/reenviar-codigo-reclamacion/
/datos-archivados/reenviar-codigo-reclamacion-tradicional/
/datos-archivados/reclamar-usuario-dinamico/<dato_id>/
```

---

## ✅ Estado del Sistema

**Completamente funcional y probado:**
- ✅ Búsqueda por email
- ✅ Verificación por código
- ✅ Reenvío de códigos
- ✅ Generación de usernames únicos
- ✅ Envío de emails
- ✅ Login automático
- ✅ Manejo de errores
- ✅ Protección contra race conditions

---

## 📝 Notas para Producción

1. Cambiar configuración de email a SMTP real
2. Configurar credenciales en `.env`
3. Cambiar `DEBUG = False` en settings.py
4. Probar envío de emails reales
5. Considerar límites de reenvío de códigos

---

**Desarrollado para Centro Fray Bartolomé de las Casas**
**Fecha**: Noviembre 2025