{
    "name": "OFITEC – Command Palette",
    "version": "16.0.1.0.0",
    "depends": ["base", "web", "mail", "project", "account", "of_proyectos", "of_aprobaciones", "of_gastos", "of_licitaciones", "of_horas", "of_presupuestos", "docuchat_ai", "ai_bridge"],
    "assets": {
        "web.assets_backend": [
            "of_command_palette/static/src/js/palette.js",
            "of_command_palette/static/src/xml/palette.xml",
            "of_command_palette/static/src/css/palette.css"
        ]
    },
    "data": ["views/ir_actions.xml"],
    "license": "LGPL-3"
}
