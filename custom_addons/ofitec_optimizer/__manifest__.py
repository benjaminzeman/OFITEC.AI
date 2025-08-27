# -*- coding: utf-8 -*-
{
    'name': 'OFITEC optimizer'.upper(),
    'version': '1.0',
    'category': 'Extra Tools',
    'summary': 'Módulo optimizer para OFITEC',
    'description': 'Módulo básico optimizer',
    'author': 'OFITEC.AI',
    'website': 'https://ofitec.ai',
    'depends': ['ofitec_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/optimizer_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
