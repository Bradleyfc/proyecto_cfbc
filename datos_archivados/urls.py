from django.urls import path
from . import views

app_name = 'datos_archivados'

urlpatterns = [
    # Dashboard principal
    path('', views.DashboardArchivadosView.as_view(), name='dashboard'),
    
    # Datos archivados dinámicos
    path('tablas/', views.TablasArchivadosListView.as_view(), name='tablas_list'),
    path('tablas/eliminar/', views.eliminar_tablas, name='eliminar_tablas'),
    path('tablas/<str:tabla>/', views.DatosArchivadosListView.as_view(), name='datos_list'),
    path('tablas/<str:tabla>/excel/', views.exportar_tabla_excel, name='exportar_tabla_excel'),
    path('datos/<int:pk>/', views.detalle_dato_archivado, name='dato_detail'),
    path('datos/<int:pk>/excel/', views.exportar_excel, name='exportar_excel'),
    
    # Migración automática
    path('migracion/configurar/', views.configurar_migracion_view, name='configurar_migracion'),
    path('migracion/estado/', views.estado_migracion_ajax, name='estado_migracion'),
    
    # Debug
    path('debug/', views.debug_permisos, name='debug_permisos'),
]