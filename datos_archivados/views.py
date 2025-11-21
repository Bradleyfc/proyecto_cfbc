from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import json

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
            
            # Estadísticas actuales basadas en datos existentes
            total_datos_actuales = DatoArchivadoDinamico.objects.count()
            total_tablas_actuales = DatoArchivadoDinamico.objects.values('tabla_origen').distinct().count()
            ultima_migracion = MigracionLog.objects.first()
            
            # Calcular estadísticas dinámicas
            if total_datos_actuales > 0:
                # Hay datos: usar estadísticas reales
                tablas_inspeccionadas = ultima_migracion.tablas_inspeccionadas if ultima_migracion else 0
                tablas_con_datos = total_tablas_actuales  # Basado en datos actuales
                tablas_vacias = max(0, tablas_inspeccionadas - tablas_con_datos)  # Calculado dinámicamente
            else:
                # No hay datos: todo en cero
                tablas_inspeccionadas = 0
                tablas_con_datos = 0
                tablas_vacias = 0
            
            # Estadísticas básicas
            context.update({
                'total_datos_archivados': total_datos_actuales,
                'total_tablas_migradas': tablas_con_datos,
                'ultima_migracion': ultima_migracion,
                'tablas_inspeccionadas_actuales': tablas_inspeccionadas,
                'tablas_vacias_actuales': tablas_vacias,
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
    """Vista para mostrar el detalle completo de un dato archivado"""
    if not tiene_permisos_datos_archivados(request.user):
        return render(request, 'datos_archivados/sin_permisos.html', status=403)
    
    try:
        from .models import DatoArchivadoDinamico
        from django.shortcuts import get_object_or_404
        import json
        
        # Obtener el dato archivado
        dato = get_object_or_404(DatoArchivadoDinamico, pk=pk)
        
        # Preparar los datos para mostrar
        context = {
            'dato': dato,
            'datos_formateados': json.dumps(dato.datos_originales, indent=2, ensure_ascii=False),
            'estructura_formateada': json.dumps(
                json.loads(dato.estructura_tabla) if dato.estructura_tabla else {}, 
                indent=2, ensure_ascii=False
            ) if dato.estructura_tabla else None,
        }
        
        return render(request, 'datos_archivados/dato_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar el detalle: {str(e)}')
        return redirect('datos_archivados:datos_list')

@method_decorator(login_required, name='dispatch')
class TablasArchivadosListView(TemplateView):
    """Vista para listar las tablas archivadas disponibles"""
    template_name = 'datos_archivados/tablas_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not tiene_permisos_datos_archivados(request.user):
            return render(request, 'datos_archivados/sin_permisos.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from .models import DatoArchivadoDinamico
            from django.db.models import Count, Max
            
            # Obtener estadísticas por tabla
            tablas_stats = DatoArchivadoDinamico.objects.values('tabla_origen').annotate(
                total_registros=Count('id'),
                ultima_migracion=Max('fecha_migracion')
            ).order_by('tabla_origen')
            
            context['tablas_stats'] = tablas_stats
            context['total_tablas'] = tablas_stats.count()
            context['total_registros'] = DatoArchivadoDinamico.objects.count()
            
        except Exception as e:
            context['tablas_stats'] = []
            context['total_tablas'] = 0
            context['total_registros'] = 0
        
        return context

@method_decorator(login_required, name='dispatch')
class DatosArchivadosListView(TemplateView):
    """Vista para listar datos archivados de una tabla específica"""
    template_name = 'datos_archivados/datos_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not tiene_permisos_datos_archivados(request.user):
            return render(request, 'datos_archivados/sin_permisos.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from .models import DatoArchivadoDinamico
            
            # Obtener la tabla desde la URL
            tabla = kwargs.get('tabla')
            
            if not tabla:
                # Si no hay tabla, redirigir a la lista de tablas
                context['datos'] = []
                context['tabla_actual'] = None
                return context
            
            # Obtener datos de la tabla específica
            queryset = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla)
            
            # Filtro de búsqueda
            search = self.request.GET.get('search')
            if search:
                queryset = queryset.filter(nombre_registro__icontains=search)
            
            context['datos'] = queryset.order_by('-fecha_migracion')
            context['tabla_actual'] = tabla
            context['total_registros'] = queryset.count()
            
        except Exception as e:
            context['datos'] = []
            context['tabla_actual'] = None
            context['total_registros'] = 0
        
        return context

@login_required
def estado_migracion_ajax(request):
    """Vista AJAX para obtener el estado de la migración actual"""
    if not tiene_permisos_datos_archivados(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        from .models import MigracionLog
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Función helper para manejar valores None
        def safe_int(value):
            return value if value is not None else 0
        
        def safe_str(value):
            return value if value is not None else ''
        
        # Buscar migración en progreso
        migracion_en_progreso = MigracionLog.objects.filter(
            estado__in=['iniciada', 'en_progreso']
        ).first()
        
        if migracion_en_progreso:
            # Calcular total de registros migrados
            total_migrados = (
                safe_int(migracion_en_progreso.usuarios_migrados) +
                safe_int(migracion_en_progreso.cursos_academicos_migrados) +
                safe_int(migracion_en_progreso.cursos_migrados) +
                safe_int(migracion_en_progreso.matriculas_migradas) +
                safe_int(migracion_en_progreso.calificaciones_migradas) +
                safe_int(migracion_en_progreso.notas_migradas) +
                safe_int(migracion_en_progreso.asistencias_migradas)
            )
            
            data = {
                'en_progreso': True,
                'estado': safe_str(migracion_en_progreso.estado) or 'iniciada',
                'fecha_inicio': migracion_en_progreso.fecha_inicio.isoformat() if migracion_en_progreso.fecha_inicio else None,
                'total_migrados': total_migrados,
                'tablas_inspeccionadas': safe_int(migracion_en_progreso.tablas_inspeccionadas),
                'tablas_con_datos': safe_int(migracion_en_progreso.tablas_con_datos),
                'tablas_vacias': safe_int(migracion_en_progreso.tablas_vacias),
                'host_origen': safe_str(migracion_en_progreso.host_origen) or 'N/A',
                'base_datos_origen': safe_str(migracion_en_progreso.base_datos_origen) or 'N/A',
            }
        else:
            # Verificar si hay una migración completada recientemente (últimos 10 minutos)
            hace_10_minutos = timezone.now() - timedelta(minutes=10)
            migracion_reciente = MigracionLog.objects.filter(
                fecha_inicio__gte=hace_10_minutos,
                estado='completada'
            ).first()
            
            if migracion_reciente:
                # Calcular total de registros migrados
                total_migrados = (
                    safe_int(migracion_reciente.usuarios_migrados) +
                    safe_int(migracion_reciente.cursos_academicos_migrados) +
                    safe_int(migracion_reciente.cursos_migrados) +
                    safe_int(migracion_reciente.matriculas_migradas) +
                    safe_int(migracion_reciente.calificaciones_migradas) +
                    safe_int(migracion_reciente.notas_migradas) +
                    safe_int(migracion_reciente.asistencias_migradas)
                )
                
                data = {
                    'en_progreso': False,
                    'completada_recientemente': True,
                    'estado': safe_str(migracion_reciente.estado) or 'completada',
                    'fecha_inicio': migracion_reciente.fecha_inicio.isoformat() if migracion_reciente.fecha_inicio else None,
                    'fecha_fin': migracion_reciente.fecha_fin.isoformat() if migracion_reciente.fecha_fin else None,
                    'total_migrados': total_migrados,
                    'tablas_inspeccionadas': safe_int(migracion_reciente.tablas_inspeccionadas),
                    'tablas_con_datos': safe_int(migracion_reciente.tablas_con_datos),
                    'tablas_vacias': safe_int(migracion_reciente.tablas_vacias),
                    'host_origen': safe_str(migracion_reciente.host_origen) or 'N/A',
                }
            else:
                data = {
                    'en_progreso': False,
                    'completada_recientemente': False,
                    'estado': 'sin_migraciones',
                    'mensaje': 'No hay migraciones registradas'
                }
        
        return JsonResponse(data)
    except Exception as e:
        # Log del error para debugging
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error en estado_migracion_ajax: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Respuesta de error segura
        return JsonResponse({
            'error': 'Error interno del servidor',
            'en_progreso': False,
            'completada_recientemente': False,
            'estado': 'error',
            'mensaje': 'Error al obtener estado de migración'
        })

@login_required
def exportar_excel(request, pk):
    """Vista para exportar un dato archivado a Excel"""
    if not tiene_permisos_datos_archivados(request.user):
        return render(request, 'datos_archivados/sin_permisos.html', status=403)
    
    try:
        from .models import DatoArchivadoDinamico
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponse
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
        import json
        from datetime import datetime
        
        # Obtener el dato archivado
        dato = get_object_or_404(DatoArchivadoDinamico, pk=pk)
        
        # Crear workbook y worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Dato_{dato.tabla_origen}_{dato.id_original}"
        
        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        info_font = Font(bold=True, color="000000")
        info_fill = PatternFill(start_color="E7F3FF", end_color="E7F3FF", fill_type="solid")
        
        # Título principal
        ws.merge_cells('A1:C1')
        ws['A1'] = f"DETALLE DEL DATO ARCHIVADO"
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Información general
        row = 3
        ws[f'A{row}'] = "INFORMACIÓN GENERAL"
        ws[f'A{row}'].font = header_font
        ws[f'A{row}'].fill = header_fill
        ws.merge_cells(f'A{row}:C{row}')
        
        row += 1
        info_data = [
            ("Tabla de Origen", dato.tabla_origen),
            ("ID Original", dato.id_original),
            ("Fecha de Migración", dato.fecha_migracion.strftime('%d/%m/%Y %H:%M:%S')),
            ("Nombre del Registro", dato.obtener_nombre_legible()),
        ]
        
        for campo, valor in info_data:
            ws[f'A{row}'] = campo
            ws[f'A{row}'].font = info_font
            ws[f'A{row}'].fill = info_fill
            ws[f'B{row}'] = str(valor)
            row += 1
        
        # Datos del registro
        row += 1
        ws[f'A{row}'] = "DATOS DEL REGISTRO"
        ws[f'A{row}'].font = header_font
        ws[f'A{row}'].fill = header_fill
        ws.merge_cells(f'A{row}:C{row}')
        
        row += 1
        ws[f'A{row}'] = "Campo"
        ws[f'B{row}'] = "Valor"
        ws[f'A{row}'].font = header_font
        ws[f'B{row}'].font = header_font
        ws[f'A{row}'].fill = header_fill
        ws[f'B{row}'].fill = header_fill
        
        # Agregar datos del registro
        for campo, valor in dato.datos_originales.items():
            row += 1
            ws[f'A{row}'] = str(campo)
            ws[f'B{row}'] = str(valor) if valor is not None else "NULL"
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Preparar respuesta HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f"dato_archivado_{dato.tabla_origen}_{dato.id_original}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Guardar workbook en response
        wb.save(response)
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al exportar a Excel: {str(e)}')
        return redirect('datos_archivados:dato_detail', pk=pk)

@login_required
def exportar_tabla_excel(request, tabla):
    """Vista para exportar todos los datos de una tabla a Excel"""
    if not tiene_permisos_datos_archivados(request.user):
        return render(request, 'datos_archivados/sin_permisos.html', status=403)
    
    try:
        from .models import DatoArchivadoDinamico
        from django.http import HttpResponse
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from datetime import datetime
        
        # Obtener todos los datos de la tabla
        datos = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).order_by('id_original')
        
        if not datos.exists():
            messages.error(request, f'No hay datos para exportar de la tabla {tabla}.')
            return redirect('datos_archivados:datos_list', tabla=tabla)
        
        # Crear workbook y worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Tabla_{tabla}"
        
        # Estilos
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        title_font = Font(bold=True, size=16, color="000000")
        info_font = Font(bold=True, size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Título principal
        ws.merge_cells('A1:F1')
        ws['A1'] = f"DATOS ARCHIVADOS - TABLA: {tabla.upper()}"
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Información de la exportación
        row = 3
        ws[f'A{row}'] = f"Fecha de exportación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        ws[f'A{row}'].font = info_font
        row += 1
        ws[f'A{row}'] = f"Total de registros: {datos.count()}"
        ws[f'A{row}'].font = info_font
        row += 1
        ws[f'A{row}'] = f"Usuario: {request.user.username}"
        ws[f'A{row}'].font = info_font
        
        # Obtener todos los campos únicos de todos los registros
        todos_los_campos = set()
        for dato in datos:
            todos_los_campos.update(dato.datos_originales.keys())
        
        campos_ordenados = sorted(list(todos_los_campos))
        
        # Headers de la tabla
        row = 6
        ws[f'A{row}'] = "ID Sistema"
        ws[f'B{row}'] = "ID Original"
        ws[f'C{row}'] = "Fecha Migración"
        
        # Agregar headers de campos dinámicos
        col_start = 4  # Columna D
        for i, campo in enumerate(campos_ordenados):
            col_letter = get_column_letter(col_start + i)
            ws[f'{col_letter}{row}'] = campo
        
        # Aplicar estilo a headers
        for col in range(1, len(campos_ordenados) + 4):
            col_letter = get_column_letter(col)
            cell = ws[f'{col_letter}{row}']
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        # Agregar datos
        for dato in datos:
            row += 1
            ws[f'A{row}'] = dato.pk
            ws[f'B{row}'] = dato.id_original
            ws[f'C{row}'] = dato.fecha_migracion.strftime('%d/%m/%Y %H:%M')
            
            # Agregar datos de campos dinámicos
            for i, campo in enumerate(campos_ordenados):
                col_letter = get_column_letter(col_start + i)
                valor = dato.datos_originales.get(campo)
                ws[f'{col_letter}{row}'] = str(valor) if valor is not None else "NULL"
            
            # Aplicar bordes a toda la fila
            for col in range(1, len(campos_ordenados) + 4):
                col_letter = get_column_letter(col)
                ws[f'{col_letter}{row}'].border = border
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)  # Máximo 30 caracteres
            ws.column_dimensions[column_letter].width = max(adjusted_width, 10)  # Mínimo 10
        
        # Preparar respuesta HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f"tabla_{tabla}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Guardar workbook en response
        wb.save(response)
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al exportar tabla a Excel: {str(e)}')
        return redirect('datos_archivados:datos_list', tabla=tabla)

@login_required
def eliminar_tablas(request):
    """Vista para eliminar tablas seleccionadas y todos sus registros"""
    if not tiene_permisos_datos_archivados(request.user):
        return render(request, 'datos_archivados/sin_permisos.html', status=403)
    
    if request.method == 'POST':
        try:
            from .models import DatoArchivadoDinamico
            
            # Obtener tablas a eliminar
            tablas = request.POST.getlist('tablas')
            
            if not tablas:
                messages.warning(request, 'No se seleccionaron tablas para eliminar.')
                return redirect('datos_archivados:tablas_list')
            
            # Contar registros antes de eliminar
            total_registros = 0
            for tabla in tablas:
                count = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).count()
                total_registros += count
            
            # Eliminar registros de las tablas seleccionadas
            eliminados = 0
            for tabla in tablas:
                eliminados += DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).delete()[0]
            
            messages.success(
                request, 
                f'Se eliminaron {len(tablas)} tabla(s) con un total de {eliminados} registros.'
            )
            
        except Exception as e:
            messages.error(request, f'Error al eliminar tablas: {str(e)}')
    
    return redirect('datos_archivados:tablas_list')

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