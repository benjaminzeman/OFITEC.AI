{
    "name": "OFITEC – Command Palette",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "web",
        "mail",
        "project",
        "ofitec_core",
        "site_management",
        "project_risk",
        "project_financials",
        "ai_bridge",
        "docuchat_ai"
    ],
    "data": [
        "views/command_palette_views.xml",
        "views/command_palette_menus.xml",
        "data/command_palette_data.xml",
        "security/ir.model.access.csv"
    ],
    "assets": {
        "web.assets_backend": [
            "of_command_palette/static/src/js/palette.js",
            "of_command_palette/static/src/xml/palette.xml",
            "of_command_palette/static/src/css/palette.css"
        ]
    },
    "license": "LGPL-3",
    "author": "OFITEC",
    "description": "Command Palette inteligente con IA integrada para gestión de proyectos de construcción."
}
