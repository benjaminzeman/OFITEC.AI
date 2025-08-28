{
    "name": "OFITEC – Next-Best-Action Dashboard",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "web",
        "project",
        "ofitec_core",
        "site_management",
        "project_risk",
        "project_financials",
        "ai_bridge",
        "of_command_palette",
        "ofitec_whatsapp",
    ],
    "data": [
        "views/next_action_views.xml",
        "views/next_action_dashboard.xml",
        "data/next_action_data.xml",
        "data/next_action_cron.xml",
        "data/whatsapp_templates.xml",
        "data/dashboard_config.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "ofitec_next_action/static/src/js/next_action.js",
            "ofitec_next_action/static/src/xml/next_action.xml",
            "ofitec_next_action/static/src/css/next_action.css",
            "ofitec_next_action/static/src/css/whatsapp_integration.css",
        ]
    },
    "license": "LGPL-3",
    "author": "OFITEC",
    "description": "Dashboard inteligente que recomienda las mejores acciones basadas en IA y análisis de datos.",
}
