# -*- coding: utf-8 -*-
"""
Advanced AI Module for OFITEC.AI
Initialization file for the AI advanced module
"""

from . import models
from . import controllers
from . import security
from . import config

# Module metadata
__version__ = "1.0.0"
__author__ = "OFITEC.AI Team"
__description__ = (
    "Advanced AI module with ML models, predictive analytics, and real-time metrics"
)

# Import main classes for easy access
from .models.ai_advanced import (
    AIAnalyticsEngine,
    AIPredictiveAnalytics,
    AIRealTimeAnalytics,
    AIAPIController,
)

from .controllers.ai_api import (
    AIAnalyticsAPI,
    AIWebhookController,
    AISecurityController,
)

from .security.ai_security import (
    AIAPIAccessLog,
    AIWebhookSecurity,
    AIEncryption,
    AISecurityAudit,
)

from .models.scaling import AIScalingConfiguration, AIMonitoringDashboard


# Initialize module
def _initialize_module():
    """Initialize the AI advanced module"""
    import logging

    _logger = logging.getLogger(__name__)
    _logger.info("Initializing Advanced AI Module v%s", __version__)


# Call initialization
_initialize_module()
