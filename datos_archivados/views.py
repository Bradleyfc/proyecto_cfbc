from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponse

def es_secretaria(user):
    """Verifica si el usuario pertenece al grupo Secretaria"""
    return user.groups.filter(name='Secretaria').exists()

def tiene_permisos_datos_archivados(user):
    """Verifica si el usuario tiene permisos para acceder a datos archivados (Secretaria o Admin)"""
    return (user.groups.filter(name='Secretaria').exists() or 
            user.is_superuser or 
            user.is_staff)

def permisos_datos_archivados_required(view_func):
    """Decorador personalizado que verifica permisos para datos archivados"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if not tiene_permisos_datos_archivados(request.user):
            return render(request, 'datos_archivados/sin_permisos.html', status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

class PermisosDataArchivadosRequiredMixin:
    """Mixin que verifica permisos para datos archivados (Secretaria o Admin)"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if not tiene_permisos_datos_archivados(request.user):
            return render(request, 'datos_archivados/sin_permisos.html', status=403)
        
        return super().dispatch(request, *args, **kwargs)

@method_decorator(login_required, name='dispatch')
class DashboardArchivadosView(TemplateView):
    """Vista principal del dashboard de datos archivados"""
    template_name = 'datos_archivados/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Verificar permisos
        if not tiene_permisos_datos_archivados(self.request.user):
            context['sin_permisos'] = True
            return context
        
        # Importar modelos aquí para evitar problemas de importación
        try:
            from .models import DatoArchivadoDinamico, MigracionLog
            
            # Estadísticas básicas
            context.update({
                'total_datos_archivados': DatoArchivadoDinamico.objects.count(),
                'total_tablas_migradas': DatoArchivadoDinamico.objects.values('tabla_origen').distinct().count(),
                'ultima_migracion': MigracionLog.objects.first(),
            })
            
            # Distribución por tabla (primeras 10)
            context['datos_por_tabla'] = DatoArchivadoDinamico.objects.values(
                'tabla_origen'
            ).annotate(
                total=Count('id')
            ).order_by('-total')[:10]
            
            # Últimas migraciones (primeras 5)
            context['ultimas_migraciones'] = MigracionLog.objects.all()[:5]
            
        except Exception as e:
            # Si hay problemas con los modelos, usar valores por defecto
            context.update({
                'total_datos_archivados': 0,
                'total_tablas_migradas': 0,
                'ultima_migracion': None,
                'datos_por_tabla': [],
                'ultimas_migraciones': [],
            })
        
        return context

@login_required
def configurar_migracion_view(request):
    """Vista para configurar y ejecutar migración automática desde MariaDB"""
    # Verificar permisos
    if not tiene_permisos_datos_archivados(request.user):
        return render(request, 'datos_archivados/sin_permisos.html', status=403)
    
    if request.method == 'POST':
        # Obtener datos de configuración
        host = request.POST.get('host')
        database = request.POST.get('database')
        user = request.POST.get('user')
        password = request.POST.get('password')
        port = request.POST.get('port', 3306)
        
        if not all([host, database, user, password]):
            messages.error(request, 'Todos los campos de conexión son obligatorios.')
            return render(request, 'datos_archivados/configurar_migracion.html')
        
        try:
            # Importar servicio aquí para evitar problemas de importación
            from .services import MigracionService
            
            # Crear servicio de migración
            servicio = MigracionService(host, database, user, password, int(port))
            
            # Probar conexión
            if not servicio.conectar_mariadb():
                messages.error(request, 'No se pudo conectar a la base de datos MariaDB. Verifique los datos de conexión.')
                return render(request, 'datos_archivados/configurar_migracion.html')
            
            servicio.desconectar_mariadb()
            
            # Ejecutar migración automática en hilo separado
            def ejecutar_migracion_automatica():
                try:
                    servicio.inspeccionar_y_migrar_automaticamente(request.user)
                except Exception as e:
                    pass  # Error handling is in the service
            
            import threading
            thread = threading.Thread(target=ejecutar_migracion_automatica)
            thread.daemon = True
            thread.start()
            
            messages.success(request, 'Migración automática iniciada correctamente. El sistema inspeccionará la base de datos y migrará todos los datos automáticamente.')
            return redirect('datos_archivados:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error al iniciar la migración: {str(e)}')
    
    return render(request, 'datos_archivados/configurar_migracion.html')

@login_required
def detalle_dato_archivado(request, pk):
    """Vista temporal para detalle"""
    if not tiene_permisos_datos_archivados(request.user):
        return render(request, 'datos_archivados/sin_permisos.html', status=403)
    
    return render(request, 'datos_archivados/dashboard.html')

@method_decorator(login_required, name='dispatch')
class DatosArchivadosListView(TemplateView):
    """Vista para listar datos archivados dinámicos"""
    template_name = 'datos_archivados/datos_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not tiene_permisos_datos_archivados(request.user):
            return render(request, 'datos_archivados/sin_permisos.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from .models import DatoArchivadoDinamico
            
            # Obtener datos con filtros
            queryset = DatoArchivadoDinamico.objects.all()
            
            tabla = self.request.GET.get('tabla')
            if tabla:
                queryset = queryset.filter(tabla_origen=tabla)
            
            search = self.request.GET.get('search')
            if search:
                queryset = queryset.filter(nombre_registro__icontains=search)
            
            context['datos'] = queryset.order_by('-fecha_migracion')[:50]  # Limitar a 50
            context['tablas_disponibles'] = DatoArchivadoDinamico.objects.values_list(
                'tabla_origen', flat=True
            ).distinct().order_by('tabla_origen')
            
        except Exception as e:
            context['datos'] = []
            context['tablas_disponibles'] = []
        
        return context

@login_required
def estado_migracion_ajax(request):
    """Vista AJAX para obtener el estado de la migración actual"""
    if not tiene_permisos_datos_archivados(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        from .models import MigracionLog
        
        ultima_migracion = MigracionLog.objects.filter(
            estado__in=['iniciada', 'en_progreso']
        ).first()
        
        if ultima_migracion:
            data = {
                'en_progreso': True,
                'estado': ultima_migracion.estado,
                'fecha_inicio': ultima_migracion.fecha_inicio.strftime('%d/%m/%Y %H:%M:%S'),
                'total_migrados': ultima_migracion.usuarios_migrados,
                'host_origen': ultima_migracion.host_origen,
                'base_datos_origen': ultima_migracion.base_datos_origen,
            }
        else:
            data = {'en_progreso': False}
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def debug_permisos(request):
    """Vista para diagnosticar permisos del usuario"""
    user = request.user
    
    # Información del usuario
    info = f"""
    <h2>Información de Debug - Usuario: {user.username}</h2>
    <p><strong>Autenticado:</strong> {user.is_authenticated}</p>
    <p><strong>Es superusuario:</strong> {user.is_superuser}</p>
    <p><strong>Es staff:</strong> {user.is_staff}</p>
    <p><strong>Grupos del usuario:</strong></p>
    <ul>
    """
    
    for grupo in user.groups.all():
        info += f"<li>{grupo.name}</li>"
    
    info += "</ul>"
    
    # Verificar específicamente el grupo Secretaria
    es_secretaria_check = user.groups.filter(name='Secretaria').exists()
    info += f"<p><strong>¿Es Secretaria?:</strong> {es_secretaria_check}</p>"
    
    # Información adicional
    info += f"""
    <p><strong>ID del usuario:</strong> {user.id}</p>
    <p><strong>Email:</strong> {user.email}</p>
    <p><strong>Nombre completo:</strong> {user.get_full_name()}</p>
    
    <hr>
    <h3>URLs de prueba:</h3>
    <p><a href="/datos-archivados/">Dashboard Datos Archivados</a></p>
    <p><a href="/datos-archivados/migracion/configurar/">Configurar Migración</a></p>
    <p><a href="/admin/">Admin Django</a></p>
    """
    
    return HttpResponse(info)