# -*- coding: utf-8 -*-
{
    'name': 'OFITEC Project Management',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Gestión avanzada de proyectos para OFITEC',
    'description': """
        Módulo de gestión de proyectos con funcionalidades avanzadas:
        - Seguimiento de proyectos
        - Gestión de tareas
        - Control de tiempo
        - Reportes de progreso
    """,
    'author': 'OFITEC.AI',
    'website': 'https://ofitec.ai',
    'depends': ['project', 'ofitec_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'data/project_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
