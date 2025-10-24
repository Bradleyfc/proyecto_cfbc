#!/usr/bin/env python
"""
Script para crear el grupo de Editores y usuarios de prueba
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from blog.models import Noticia, Categoria, Comentario

def crear_grupo_editores():
    print("Configurando grupo de Editores...")
    
    # Crear grupo Editores
    grupo_editores, created = Group.objects.get_or_create(name='Editores')
    if created:
        print("✓ Grupo 'Editores' creado")
    else:
        print("✓ Grupo 'Editores' ya existe")
    
    # Obtener permisos para el blog
    content_types = [
        ContentType.objects.get_for_model(Noticia),
        ContentType.objects.get_for_model(Categoria),
        ContentType.objects.get_for_model(Comentario),
    ]
    
    permisos_editores = []
    for ct in content_types:
        permisos = Permission.objects.filter(content_type=ct)
        permisos_editores.extend(permisos)
    
    # Asignar permisos al grupo
    grupo_editores.permissions.set(permisos_editores)
    print(f"✓ Asignados {len(permisos_editores)} permisos al grupo Editores")
    
    # Crear usuario editor de prueba
    editor_user, created = User.objects.get_or_create(
        username='editor',
        defaults={
            'email': 'editor@cfbc.edu.ni',
            'first_name': 'Editor',
            'last_name': 'CFBC',
            'is_staff': False,
            'is_active': True
        }
    )
    
    if created:
        editor_user.set_password('editor123')
        editor_user.save()
        print("✓ Usuario 'editor' creado")
    else:
        print("✓ Usuario 'editor' ya existe")
    
    # Agregar usuario al grupo
    editor_user.groups.add(grupo_editores)
    print("✓ Usuario 'editor' agregado al grupo Editores")
    
    # Crear otro usuario editor
    editor2_user, created = User.objects.get_or_create(
        username='redactor',
        defaults={
            'email': 'redactor@cfbc.edu.ni',
            'first_name': 'María',
            'last_name': 'Redactora',
            'is_staff': False,
            'is_active': True
        }
    )
    
    if created:
        editor2_user.set_password('redactor123')
        editor2_user.save()
        print("✓ Usuario 'redactor' creado")
    else:
        print("✓ Usuario 'redactor' ya existe")
    
    # Agregar usuario al grupo
    editor2_user.groups.add(grupo_editores)
    print("✓ Usuario 'redactor' agregado al grupo Editores")
    
    print("\n¡Configuración completada!")
    print("\nUsuarios editores creados:")
    print("1. Usuario: editor | Contraseña: editor123")
    print("2. Usuario: redactor | Contraseña: redactor123")
    print("\nPueden acceder al panel de editores en: http://localhost:8000/noticias/editores/")
    print("También pueden ver el enlace 'Panel de Editores' en el menú de usuario cuando inicien sesión.")

if __name__ == '__main__':
    crear_grupo_editores()