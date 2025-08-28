# -*- coding: utf-8 -*-
{
    "name": "OFITEC backup",
    "version": "1.0",
    "category": "Extra Tools",
    "summary": "Módulo backup para OFITEC",
    "description": "Módulo básico backup",
    "author": "OFITEC.AI",
    "website": "https://ofitec.ai",
    "depends": ["ofitec_core"],
    "data": [
        "security/ir.model.access.csv",
        "views/backup_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
