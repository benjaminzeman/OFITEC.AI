# -*- coding: utf-8 -*-
"""
REST API Controller for Advanced AI Module
Provides endpoints for ML predictions, analytics, and real-time data
"""

import logging
from datetime import datetime
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AIAnalyticsAPI(http.Controller):
    """REST API Controller for AI Analytics"""

    @http.route("/api/v1/ai/predict", type="json", auth="user", methods=["POST"])
    def predict(self, **kwargs):
        """Predict using trained ML models"""
        try:
            data = request.jsonrequest

            if not data or "model_type" not in data:
                return self._error_response("Missing model_type parameter")

            model_type = data["model_type"]
            features = data.get("features", [])

            # Get AI analytics model
            ai_model = request.env["ofitec.ai.analytics"].search(
                [
                    ("model_type", "=", model_type),
                    ("is_active", "=", True),
                    ("is_trained", "=", True),
                ],
                limit=1,
            )

            if not ai_model:
                return self._error_response(
                    f"No trained model found for type: {model_type}"
                )

            # Make prediction
            prediction = ai_model.predict(features)

            return self._success_response(
                {
                    "prediction": prediction,
                    "model_name": ai_model.model_name,
                    "confidence": ai_model.accuracy_score,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            _logger.error(f"Prediction API error: {e}")
            return self._error_response(str(e))

    @http.route(
        "/api/v1/ai/analytics/predictive", type="json", auth="user", methods=["GET"]
    )
    def get_predictive_analytics(self, **kwargs):
        """Get predictive analytics for projects"""
        try:
            project_id = kwargs.get("project_id")

            predictive = request.env["ofitec.ai.predictive"]
            results = predictive.run_predictive_analysis(project_id)

            return self._success_response(
                {
                    "results": results,
                    "count": len(results),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            _logger.error(f"Predictive analytics API error: {e}")
            return self._error_response(str(e))

    @http.route(
        "/api/v1/ai/analytics/realtime", type="json", auth="user", methods=["GET"]
    )
    def get_realtime_analytics(self, **kwargs):
        """Get real-time analytics metrics"""
        try:
            api_controller = request.env["ofitec.ai.api"]
            metrics = api_controller.get_realtime_metrics()

            return self._success_response(
                {"metrics": metrics, "timestamp": datetime.now().isoformat()}
            )

        except Exception as e:
            _logger.error(f"Real-time analytics API error: {e}")
            return self._error_response(str(e))

    @http.route("/api/v1/ai/models", type="json", auth="user", methods=["GET"])
    def list_models(self, **kwargs):
        """List available AI models"""
        try:
            models = request.env["ofitec.ai.analytics"].search(
                [("is_active", "=", True)]
            )

            model_list = []
            for model in models:
                model_list.append(
                    {
                        "id": model.id,
                        "name": model.model_name,
                        "type": model.model_type,
                        "algorithm": model.algorithm,
                        "is_trained": model.is_trained,
                        "accuracy": model.accuracy_score,
                        "last_trained": model.training_date
                        and model.training_date.isoformat(),
                    }
                )

            return self._success_response(
                {"models": model_list, "count": len(model_list)}
            )

        except Exception as e:
            _logger.error(f"List models API error: {e}")
            return self._error_response(str(e))

    @http.route(
        "/api/v1/ai/models/<int:model_id>/train",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def train_model(self, model_id, **kwargs):
        """Train specific AI model"""
        try:
            model = request.env["ofitec.ai.analytics"].browse(model_id)

            if not model.exists():
                return self._error_response("Model not found")

            result = model.train_model()

            return self._success_response(result)

        except Exception as e:
            _logger.error(f"Train model API error: {e}")
            return self._error_response(str(e))

    @http.route(
        "/api/v1/ai/models/<int:model_id>/features",
        type="json",
        auth="user",
        methods=["GET"],
    )
    def get_model_features(self, model_id, **kwargs):
        """Get feature importance for trained model"""
        try:
            model = request.env["ofitec.ai.analytics"].browse(model_id)

            if not model.exists():
                return self._error_response("Model not found")

            if not model.is_trained:
                return self._error_response("Model is not trained")

            features = model.get_feature_importance()

            return self._success_response(
                {"model_name": model.model_name, "features": features}
            )

        except Exception as e:
            _logger.error(f"Get model features API error: {e}")
            return self._error_response(str(e))

    @http.route(
        "/api/v1/ai/insights/<int:project_id>",
        type="json",
        auth="user",
        methods=["GET"],
    )
    def get_project_insights(self, project_id, **kwargs):
        """Get AI insights for specific project"""
        try:
            project = request.env["project.project"].browse(project_id)

            if not project.exists():
                return self._error_response("Project not found")

            # Get predictive analysis
            predictive = request.env["ofitec.ai.predictive"]
            analysis = predictive._analyze_project(project)

            # Get real-time metrics for this project
            realtime_metrics = request.env["ofitec.ai.realtime"].search(
                [("metric_name", "ilike", project.name)]
            )

            metrics_data = []
            for metric in realtime_metrics:
                metrics_data.append(
                    {
                        "name": metric.metric_name,
                        "value": metric.current_value,
                        "target": metric.target_value,
                        "status": metric.status,
                        "trend": metric.trend,
                    }
                )

            return self._success_response(
                {
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "status": (
                            project.stage_id.name if project.stage_id else "Unknown"
                        ),
                    },
                    "predictive_analysis": analysis,
                    "realtime_metrics": metrics_data,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            _logger.error(f"Get project insights API error: {e}")
            return self._error_response(str(e))

    @http.route(
        "/api/v1/ai/dashboard/summary", type="json", auth="user", methods=["GET"]
    )
    def get_dashboard_summary(self, **kwargs):
        """Get comprehensive dashboard summary"""
        try:
            # Get overall metrics
            api_controller = request.env["ofitec.ai.api"]
            realtime_metrics = api_controller.get_realtime_metrics()

            # Get predictive insights
            predictive_insights = api_controller.get_predictive_insights()

            # Get model status
            models = request.env["ofitec.ai.analytics"].search(
                [("is_active", "=", True)]
            )

            model_status = []
            for model in models:
                model_status.append(
                    {
                        "name": model.model_name,
                        "type": model.model_type,
                        "trained": model.is_trained,
                        "accuracy": model.accuracy_score,
                    }
                )

            # Calculate summary statistics
            total_projects = request.env["project.project"].search_count([])
            active_projects = request.env["project.project"].search_count(
                [("stage_id.name", "not in", ["Done", "Cancelled"])]
            )
            completed_projects = request.env["project.project"].search_count(
                [("stage_id.name", "=", "Done")]
            )

            return self._success_response(
                {
                    "summary": {
                        "total_projects": total_projects,
                        "active_projects": active_projects,
                        "completed_projects": completed_projects,
                        "completion_rate": (
                            (completed_projects / total_projects * 100)
                            if total_projects > 0
                            else 0
                        ),
                    },
                    "realtime_metrics": realtime_metrics,
                    "predictive_insights": predictive_insights,
                    "model_status": model_status,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            _logger.error(f"Dashboard summary API error: {e}")
            return self._error_response(str(e))

    @http.route(
        "/api/v1/ai/webhook/<string:service>",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def webhook_handler(self, service, **kwargs):
        """Handle webhooks from external services"""
        try:
            data = request.jsonrequest

            if service == "powerbi":
                return self._handle_powerbi_webhook(data)
            elif service == "tableau":
                return self._handle_tableau_webhook(data)
            elif service == "slack":
                return self._handle_slack_webhook(data)
            else:
                return self._error_response(f"Unknown service: {service}")

        except Exception as e:
            _logger.error(f"Webhook handler error for {service}: {e}")
            return self._error_response(str(e))

    def _handle_powerbi_webhook(self, data):
        """Handle Power BI webhook data"""
        # Process Power BI dataset refresh notifications
        _logger.info(f"Power BI webhook received: {data}")

        # Update real-time metrics based on Power BI data
        # This would integrate with Power BI REST API

        return self._success_response({"status": "processed", "service": "powerbi"})

    def _handle_tableau_webhook(self, data):
        """Handle Tableau webhook data"""
        # Process Tableau view refresh notifications
        _logger.info(f"Tableau webhook received: {data}")

        # Update analytics based on Tableau data
        # This would integrate with Tableau REST API

        return self._success_response({"status": "processed", "service": "tableau"})

    def _handle_slack_webhook(self, data):
        """Handle Slack webhook data"""
        # Process Slack notifications and alerts
        _logger.info(f"Slack webhook received: {data}")

        # Send AI insights to Slack channels
        # This would integrate with Slack API

        return self._success_response({"status": "processed", "service": "slack"})

    def _success_response(self, data):
        """Return success response"""
        return {"status": "success", "data": data}

    def _error_response(self, message, status_code=400):
        """Return error response"""
        return {
            "status": "error",
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }


class AIWebhookController(http.Controller):
    """Webhook Controller for External Integrations"""

    @http.route(
        "/api/v1/ai/webhook/powerbi/refresh",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def powerbi_dataset_refresh(self, **kwargs):
        """Handle Power BI dataset refresh webhook"""
        try:
            data = request.jsonrequest

            # Log the refresh event
            _logger.info(f"Power BI dataset refresh: {data}")

            # Update real-time metrics
            realtime = request.env["ofitec.ai.realtime"]
            realtime.update_realtime_metrics()

            # Trigger predictive analysis update
            predictive = request.env["ofitec.ai.predictive"]
            predictive.run_predictive_analysis()

            return {
                "status": "success",
                "message": "Power BI refresh processed successfully",
            }

        except Exception as e:
            _logger.error(f"Power BI webhook error: {e}")
            return {"status": "error", "message": str(e)}

    @http.route(
        "/api/v1/ai/webhook/tableau/alert",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def tableau_alert_webhook(self, **kwargs):
        """Handle Tableau alert webhook"""
        try:
            data = request.jsonrequest

            # Process Tableau alert
            _logger.info(f"Tableau alert: {data}")

            # Create notification in Odoo
            if data.get("alert_name") and data.get("message"):
                request.env["mail.message"].create(
                    {
                        "subject": f"Tableau Alert: {data['alert_name']}",
                        "body": data["message"],
                        "message_type": "notification",
                        "subtype_id": request.env.ref("mail.mt_note").id,
                    }
                )

            return {
                "status": "success",
                "message": "Tableau alert processed successfully",
            }

        except Exception as e:
            _logger.error(f"Tableau webhook error: {e}")
            return {"status": "error", "message": str(e)}


class AISecurityController(http.Controller):
    """Security Controller for AI API"""

    @http.route(
        "/api/v1/ai/auth/token",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def get_auth_token(self, **kwargs):
        """Get authentication token for API access"""
        try:
            data = request.jsonrequest

            if not data or "username" not in data or "password" not in data:
                return self._error_response("Missing username or password")

            # Authenticate user
            user = (
                request.env["res.users"]
                .sudo()
                .search([("login", "=", data["username"])], limit=1)
            )

            if not user or not user.check_password(data["password"]):
                return self._error_response("Invalid credentials")

            # Generate token (simplified - in production use JWT or OAuth)
            token = user._generate_api_token()

            return self._success_response(
                {"token": token, "user_id": user.id, "expires_in": 3600}  # 1 hour
            )

        except Exception as e:
            _logger.error(f"Auth token error: {e}")
            return self._error_response(str(e))

    def _success_response(self, data):
        """Return success response"""
        return {"status": "success", "data": data}

    def _error_response(self, message):
        """Return error response"""
        return {"status": "error", "message": message}
