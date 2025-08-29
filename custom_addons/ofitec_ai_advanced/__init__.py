# -*- coding: utf-8 -*-
"""
Advanced AI Module for OFITEC.AI
Initialization file for the AI advanced module
"""

from . import models  # noqa: F401
from . import controllers  # noqa: F401
from . import security  # noqa: F401
from . import config  # noqa: F401

# Module metadata
__version__ = "1.0.0"
__author__ = "OFITEC.AI Team"
__description__ = (
    "Advanced AI module with ML models, predictive analytics, and real-time metrics"
)

# Import main classes for easy access
from .models.ai_advanced import (  # noqa: F401
    AIAnalyticsEngine,
    AIPredictiveAnalytics,
    AIRealTimeAnalytics,
    AIAPIController,
)

from .controllers.ai_api import (  # noqa: F401
    AIAnalyticsAPI,
    AIWebhookController,
    AISecurityController,
)

from .security.ai_security import (  # noqa: F401
    AIAPIAccessLog,
    AIWebhookSecurity,
    AIEncryption,
    AISecurityAudit,
)

from .models.scaling import (  # noqa: F401
    AIScalingConfiguration,
    AIMonitoringDashboard,
)


# Initialize module
def _initialize_module():
    """Initialize the AI advanced module"""
    import logging

    _logger = logging.getLogger(__name__)
    _logger.info("Initializing Advanced AI Module v%s", __version__)


# Call initialization
_initialize_module()
