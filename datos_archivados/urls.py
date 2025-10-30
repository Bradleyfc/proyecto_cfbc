from django.urls import path
from . import views

app_name = 'datos_archivados'

urlpatterns = [
    # Dashboard principal
    path('', views.DashboardArchivadosView.as_view(), name='dashboard'),
    
    # Datos archivados dinámicos
    path('datos/', views.DatosArchivadosListView.as_view(), name='datos_list'),
    path('datos/<int:pk>/', views.detalle_dato_archivado, name='dato_detail'),
    
    # Migración automática
    path('migracion/configurar/', views.configurar_migracion_view, name='configurar_migracion'),
    path('migracion/estado/', views.estado_migracion_ajax, name='estado_migracion'),
    
    # Debug
    path('debug/', views.debug_permisos, name='debug_permisos'),
]