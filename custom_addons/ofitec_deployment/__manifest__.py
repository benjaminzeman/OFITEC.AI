# -*- coding: utf-8 -*-
{
    "name": "OFITEC deployment",
    "version": "1.0",
    "category": "Extra Tools",
    "summary": "Módulo deployment para OFITEC",
    "description": "Módulo básico deployment",
    "author": "OFITEC.AI",
    "website": "https://ofitec.ai",
    "depends": ["ofitec_core"],
    "data": [
        "security/ir.model.access.csv",
        "views/deployment_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
