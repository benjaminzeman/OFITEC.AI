{
    "name": "OFITEC Theme",
    "version": "16.0.1.0.0",
    "category": "Theme/Backend",
    "summary": "Tema corporativo OFITEC con modo claro y oscuro",
    "author": "OFITEC",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [],
    "assets": {
        "web._assets_primary_variables": [
            "ofitec_theme/static/src/scss/brand_variables.scss",
        ],
        "web.assets_backend": [
            "ofitec_theme/static/src/scss/light_theme.scss",
            "ofitec_theme/static/src/scss/dark_theme.scss",
            "ofitec_theme/static/src/scss/components.scss",
            "ofitec_theme/static/src/js/theme_switch.js",
            "ofitec_theme/static/src/js/chart_palette.js",
            # Opcional: estilos base anteriores
            "ofitec_theme/static/src/css/ofitec_base.scss",
        ]
    },
    "installable": True,
    "auto_install": True,
    "application": False,
    "description": "Interfaz visual adaptada al branding de OFITEC con soporte light/dark.",
}
