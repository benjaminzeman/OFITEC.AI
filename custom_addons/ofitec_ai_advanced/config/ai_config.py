# Configuration file for Advanced AI Module
# This file contains default settings and can be overridden

# AI Model Configuration
AI_MODELS = {
    'cost_prediction': {
        'algorithm': 'xgboost',
        'parameters': {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1
        },
        'training_data_size': 1000
    },
    'risk_assessment': {
        'algorithm': 'random_forest',
        'parameters': {
            'n_estimators': 100,
            'max_depth': 10
        },
        'training_data_size': 500
    },
    'schedule_forecast': {
        'algorithm': 'lightgbm',
        'parameters': {
            'num_leaves': 31,
            'learning_rate': 0.1,
            'n_estimators': 100
        },
        'training_data_size': 800
    }
}

# Real-time Metrics Configuration
REALTIME_METRICS = {
    'kpi_completion': {
        'type': 'kpi',
        'target': 85.0,
        'update_interval': 300  # 5 minutes
    },
    'performance_score': {
        'type': 'performance',
        'target': 90.0,
        'update_interval': 300
    },
    'quality_score': {
        'type': 'quality',
        'target': 95.0,
        'update_interval': 600  # 10 minutes
    },
    'risk_level': {
        'type': 'risk',
        'target': 2.0,
        'update_interval': 300
    }
}

# API Configuration
API_CONFIG = {
    'base_url': '/api/v1/ai',
    'auth_required': True,
    'rate_limit': 100,  # requests per hour
    'cors_origins': ['*'],  # Configure appropriately for production
    'swagger_enabled': True,
    'api_version': 'v1'
}

# Cache Configuration
CACHE_CONFIG = {
    'redis_host': 'localhost',
    'redis_port': 6379,
    'redis_db': 0,
    'ttl': 3600,  # 1 hour
    'max_size': 512  # MB
}

# Webhook Configuration
WEBHOOK_CONFIG = {
    'powerbi': {
        'url': 'https://api.powerbi.com/webhooks',
        'secret': 'your_powerbi_webhook_secret',
        'rate_limit': 100
    },
    'tableau': {
        'url': 'https://api.tableau.com/webhooks',
        'secret': 'your_tableau_webhook_secret',
        'rate_limit': 50
    },
    'slack': {
        'url': 'https://hooks.slack.com/services/your/slack/webhook',
        'secret': 'your_slack_webhook_secret',
        'rate_limit': 200
    }
}

# Security Configuration
SECURITY_CONFIG = {
    'encryption_key': None,  # Set in production environment
    'token_expiry': 3600,  # 1 hour
    'max_login_attempts': 5,
    'lockout_duration': 900,  # 15 minutes
    'audit_log_retention': 90  # days
}

# Scaling Configuration
SCALING_CONFIG = {
    'enable_load_balancing': False,
    'worker_nodes': [],
    'load_balancing_strategy': 'round_robin',
    'enable_monitoring': True,
    'monitoring_interval': 60,
    'enable_auto_scaling': False,
    'min_workers': 2,
    'max_workers': 10,
    'scale_up_threshold': 75.0,
    'scale_down_threshold': 25.0
}

# Alert Configuration
ALERT_CONFIG = {
    'cpu_threshold': 80.0,
    'memory_threshold': 85.0,
    'response_time_threshold': 1000.0,
    'email_alerts': True,
    'slack_alerts': True,
    'sms_alerts': False
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'file': '/var/log/odoo/ai_advanced.log',
    'max_size': 10485760,  # 10MB
    'backup_count': 5,
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Feature Flags
FEATURE_FLAGS = {
    'enable_predictive_analytics': True,
    'enable_realtime_metrics': True,
    'enable_ml_models': True,
    'enable_api_access': True,
    'enable_webhooks': True,
    'enable_scaling': False,
    'enable_monitoring': True,
    'enable_security_audit': True
}
