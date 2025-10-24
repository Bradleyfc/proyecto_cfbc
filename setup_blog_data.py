#!/usr/bin/env python
"""
Script para crear datos de prueba para el blog de noticias
"""
import os
import django
from django.utils import timezone
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Categoria, Noticia

def crear_datos_blog():
    print("Creando datos de prueba para las noticias...")
    
    # Crear usuario admin si no existe
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@cfbc.edu.ni',
            'first_name': 'Administrador',
            'last_name': 'CFBC',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✓ Usuario admin creado")
    else:
        print(f"✓ Usuario admin ya existe")
    
    # Crear categorías
    categorias_data = [
        {
            'nombre': 'Noticias Institucionales',
            'descripcion': 'Noticias oficiales y comunicados de la institución'
        },
        {
            'nombre': 'Eventos Académicos',
            'descripcion': 'Conferencias, seminarios y actividades académicas'
        },
        {
            'nombre': 'Vida Estudiantil',
            'descripcion': 'Actividades y logros de nuestros estudiantes'
        },
        {
            'nombre': 'Investigación',
            'descripcion': 'Proyectos de investigación y publicaciones'
        },
        {
            'nombre': 'Extensión Social',
            'descripcion': 'Proyectos de extensión y responsabilidad social'
        }
    ]
    
    categorias_creadas = []
    for cat_data in categorias_data:
        categoria, created = Categoria.objects.get_or_create(
            nombre=cat_data['nombre'],
            defaults={'descripcion': cat_data['descripcion']}
        )
        categorias_creadas.append(categoria)
        if created:
            print(f"✓ Categoría '{categoria.nombre}' creada")
        else:
            print(f"✓ Categoría '{categoria.nombre}' ya existe")
    
    # Crear noticias de ejemplo
    noticias_data = [
        {
            'titulo': 'Inauguración del Nuevo Laboratorio de Computación',
            'resumen': 'El Centro Fray Bartolomé de las Casas inaugura un moderno laboratorio de computación equipado con la última tecnología.',
            'contenido': '''El pasado viernes se llevó a cabo la inauguración del nuevo laboratorio de computación del Centro Fray Bartolomé de las Casas. Este espacio cuenta con 30 computadoras de última generación, proyectores interactivos y conexión de alta velocidad a internet.

El laboratorio beneficiará a más de 500 estudiantes de diferentes carreras, especialmente aquellos de las áreas de informática, administración y contabilidad. La inversión realizada asciende a $50,000 dólares y fue posible gracias al apoyo de organizaciones internacionales.

Durante la ceremonia de inauguración estuvieron presentes autoridades académicas, estudiantes y representantes de la comunidad. El director del centro destacó la importancia de contar con herramientas tecnológicas modernas para brindar una educación de calidad.

"Este laboratorio representa nuestro compromiso con la excelencia académica y la formación integral de nuestros estudiantes", expresó el director durante su discurso inaugural.''',
            'categoria': 0,  # Noticias Institucionales
            'destacada': True
        },
        {
            'titulo': 'Conferencia Internacional sobre Derechos Humanos',
            'resumen': 'Expertos internacionales se reunirán en nuestro centro para discutir los desafíos actuales en materia de derechos humanos.',
            'contenido': '''El próximo mes se realizará la "III Conferencia Internacional sobre Derechos Humanos en América Latina" en las instalaciones del Centro Fray Bartolomé de las Casas.

El evento contará con la participación de reconocidos académicos, activistas y representantes de organizaciones internacionales de derechos humanos. Durante tres días se abordarán temas como la protección de defensores de derechos humanos, justicia transicional y el papel de la sociedad civil.

Entre los ponentes confirmados se encuentran la Dra. María González, relatora especial de la ONU, y el Dr. Carlos Martínez, director del Instituto Interamericano de Derechos Humanos.

La conferencia es gratuita y está abierta al público en general. Los interesados pueden registrarse a través de nuestro sitio web o en las oficinas del centro.''',
            'categoria': 1,  # Eventos Académicos
            'destacada': True
        },
        {
            'titulo': 'Estudiantes Ganan Concurso Nacional de Debate',
            'resumen': 'El equipo de debate del CFBC obtuvo el primer lugar en el concurso nacional universitario.',
            'contenido': '''Un grupo de estudiantes del Centro Fray Bartolomé de las Casas se alzó con el primer lugar en el XV Concurso Nacional Universitario de Debate, celebrado en la capital del país.

El equipo, conformado por Ana Rodríguez, Carlos Mendoza y Patricia López, compitió contra 25 universidades de todo el país. El tema central del debate fue "El papel de la educación en la construcción de la paz".

Los estudiantes fueron preparados por el profesor de filosofía, Dr. Roberto Sánchez, quien destacó el compromiso y dedicación del equipo durante los meses de preparación.

"Estamos muy orgullosos de nuestros estudiantes. Este triunfo refleja la calidad académica de nuestro centro y el compromiso de nuestros jóvenes con los temas sociales", expresó el coordinador académico.

Como premio, los estudiantes recibirán becas parciales para continuar sus estudios y representarán al país en el concurso centroamericano que se realizará el próximo año.''',
            'categoria': 2,  # Vida Estudiantil
            'destacada': False
        },
        {
            'titulo': 'Nuevo Proyecto de Investigación sobre Cambio Climático',
            'resumen': 'Investigadores del CFBC inician un ambicioso proyecto para estudiar los efectos del cambio climático en comunidades rurales.',
            'contenido': '''El Centro de Investigación del CFBC ha dado inicio a un nuevo proyecto de investigación titulado "Impacto del Cambio Climático en Comunidades Rurales de Nicaragua".

El proyecto, que tendrá una duración de dos años, cuenta con financiamiento de la Unión Europea y será dirigido por la Dra. Elena Vargas, especialista en estudios ambientales.

La investigación se realizará en cinco comunidades rurales del país y tiene como objetivo documentar los efectos del cambio climático en la agricultura, los recursos hídricos y las condiciones de vida de las familias campesinas.

"Este estudio nos permitirá generar información valiosa para el diseño de políticas públicas que ayuden a las comunidades a adaptarse al cambio climático", explicó la directora del proyecto.

El equipo de investigación está conformado por docentes y estudiantes de último año de las carreras de sociología, trabajo social y desarrollo rural.''',
            'categoria': 3,  # Investigación
            'destacada': False
        },
        {
            'titulo': 'Campaña de Alfabetización en Comunidades Rurales',
            'resumen': 'Estudiantes y docentes del CFBC llevan educación a comunidades rurales a través de un programa de alfabetización.',
            'contenido': '''El Centro Fray Bartolomé de las Casas ha puesto en marcha una nueva campaña de alfabetización dirigida a adultos de comunidades rurales del departamento.

El programa "Educación para Todos" beneficiará a más de 200 personas adultas que no tuvieron la oportunidad de aprender a leer y escribir en su infancia. Las clases se imparten los fines de semana en centros comunitarios y escuelas rurales.

Un grupo de 30 estudiantes voluntarios, supervisados por docentes del centro, se desplazan cada sábado a las comunidades para impartir las clases. El programa incluye no solo alfabetización básica, sino también nociones de matemáticas y educación cívica.

"Es emocionante ver cómo personas de 60 o 70 años aprenden a escribir su nombre por primera vez. Esto nos recuerda por qué elegimos la educación como nuestra vocación", comentó María Pérez, estudiante de pedagogía y voluntaria del programa.

La campaña se extenderá por seis meses y al finalizar se realizará una ceremonia de graduación para celebrar los logros de los participantes.''',
            'categoria': 4,  # Extensión Social
            'destacada': True
        }
    ]
    
    # Crear las noticias
    for i, noticia_data in enumerate(noticias_data):
        fecha_pub = timezone.now() - timedelta(days=i*3)  # Espaciar las fechas
        
        noticia, created = Noticia.objects.get_or_create(
            titulo=noticia_data['titulo'],
            defaults={
                'resumen': noticia_data['resumen'],
                'contenido': noticia_data['contenido'],
                'categoria': categorias_creadas[noticia_data['categoria']],
                'autor': admin_user,
                'estado': 'publicado',
                'destacada': noticia_data['destacada'],
                'fecha_publicacion': fecha_pub
            }
        )
        
        if created:
            print(f"✓ Noticia '{noticia.titulo}' creada")
        else:
            print(f"✓ Noticia '{noticia.titulo}' ya existe")
    
    print("\n¡Datos de prueba creados exitosamente!")
    print("\nPuedes acceder a las noticias en: http://localhost:8000/noticias/")
    print("Para administrar el contenido: http://localhost:8000/admin/")
    print("Usuario: admin")
    print("Contraseña: admin123")

if __name__ == '__main__':
    crear_datos_blog()