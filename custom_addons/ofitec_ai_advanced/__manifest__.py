{
    "name": "OFITEC – Advanced AI & Analytics",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
        "web",
        "ofitec_core",
        "project",
        "board"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/ai_views.xml",
        "data/ai_data.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "ofitec_ai_advanced/static/src/js/ai_dashboard.js",
            "ofitec_ai_advanced/static/src/xml/ai_dashboard.xml"
        ]
    },
    "external_dependencies": {
        "python": [
            "scikit-learn",
            "pandas",
            "numpy",
            "matplotlib",
            "seaborn",
            "requests",
            "tensorflow",
            "xgboost",
            "lightgbm"
        ]
    },
    "license": "LGPL-3",
    "author": "OFITEC",
    "description": "Sistema avanzado de IA con modelos de ML predictivos, analytics en tiempo real, API REST completa y escalabilidad horizontal."
}
