{
    "name": "OFITEC – WhatsApp Business Integration",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "web",
        "ofitec_core",
        "ofitec_next_action",
        "mail"
    ],
    "data": [
        "views/whatsapp_views.xml",
        "data/whatsapp_data.xml",
        "data/whatsapp_config.xml",
        "security/ir.model.access.csv",
        "security/whatsapp_security.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "ofitec_whatsapp/static/src/js/whatsapp.js",
            "ofitec_whatsapp/static/src/css/whatsapp.css"
        ]
    },
    "external_dependencies": {
        "python": ["requests", "twilio"]
    },
    "license": "LGPL-3",
    "author": "OFITEC",
    "description": "Integración completa con WhatsApp Business API para notificaciones inteligentes y comunicación bidireccional."
}
