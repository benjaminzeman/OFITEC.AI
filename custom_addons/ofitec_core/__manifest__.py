{
    "name": "OFITEC Core",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "project",
        "account",
        "hr",
        "mail",
        "bus"
    ],
    "data": [
        "views/core_views.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "ofitec_core/static/src/js/executive_dashboard.js"
        ]
    },
    "license": "LGPL-3",
    "author": "OFITEC",
    "description": "Módulo central de OFITEC con API, modelos, dashboard y utilidades (GraphQL opcional y métricas Prometheus)."
}
