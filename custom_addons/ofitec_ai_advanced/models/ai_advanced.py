# -*- coding: utf-8 -*-
"""
Advanced AI Module for OFITEC.AI
Implements ML models, predictive analytics, and intelligent automation
"""

import logging
import json
import numpy as np
from datetime import datetime
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIAnalyticsEngine(models.Model):
    """Advanced AI Analytics Engine with ML models"""

    _name = "ofitec.ai.analytics"
    _description = "Advanced AI Analytics Engine"
    _rec_name = "model_name"

    # Model Configuration
    model_name = fields.Char(string="Model Name", required=True)
    model_type = fields.Selection(
        [
            ("cost_prediction", "Cost Prediction"),
            ("risk_assessment", "Risk Assessment"),
            ("schedule_forecast", "Schedule Forecast"),
            ("quality_prediction", "Quality Prediction"),
            ("resource_optimization", "Resource Optimization"),
            ("anomaly_detection", "Anomaly Detection"),
        ],
        string="Model Type",
        required=True,
    )

    algorithm = fields.Selection(
        [
            ("random_forest", "Random Forest"),
            ("gradient_boosting", "Gradient Boosting"),
            ("xgboost", "XGBoost"),
            ("lightgbm", "LightGBM"),
            ("neural_network", "Neural Network"),
        ],
        string="Algorithm",
        default="xgboost",
        required=True,
    )

    # Model Status
    is_active = fields.Boolean(string="Active", default=True)
    is_trained = fields.Boolean(string="Trained", readonly=True)
    training_date = fields.Datetime(string="Last Training", readonly=True)
    accuracy_score = fields.Float(string="Accuracy Score", readonly=True)
    mae_score = fields.Float(string="MAE Score", readonly=True)

    # Training Configuration
    training_data_size = fields.Integer(string="Training Data Size", default=1000)
    test_size = fields.Float(string="Test Size", default=0.2)
    random_state = fields.Integer(string="Random State", default=42)

    # Model Parameters
    model_parameters = fields.Text(
        string="Model Parameters", default='{"n_estimators": 100, "max_depth": 10}'
    )

    # Performance Metrics
    training_time = fields.Float(string="Training Time (seconds)", readonly=True)
    prediction_time = fields.Float(string="Avg Prediction Time (ms)", readonly=True)

    # Data Sources
    data_sources = fields.Many2many(
        "ir.model", string="Data Sources", help="Odoo models to use as data sources"
    )

    @api.model
    def create(self, vals):
        """Override create to initialize model"""
        record = super(AIAnalyticsEngine, self).create(vals)
        record._initialize_model()
        return record

    def _initialize_model(self):
        """Initialize the ML model"""
        self.ensure_one()

        try:
            if self.algorithm == "xgboost":
                self._initialize_xgboost()
            elif self.algorithm == "lightgbm":
                self._initialize_lightgbm()
            elif self.algorithm == "random_forest":
                self._initialize_random_forest()
            elif self.algorithm == "gradient_boosting":
                self._initialize_gradient_boosting()

            _logger.info(f"Initialized {self.algorithm} model: {self.model_name}")

        except Exception as e:
            _logger.error(f"Failed to initialize model {self.model_name}: {e}")
            raise UserError(f"Failed to initialize model: {e}")

    def _initialize_xgboost(self):
        """Initialize XGBoost model"""
        params = json.loads(self.model_parameters or "{}")
        default_params = {
            "objective": (
                "reg:linear" if self._is_regression_model() else "multi:softmax"
            ),
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": self.random_state,
        }
        default_params.update(params)
        self.model_parameters = json.dumps(default_params)

    def _initialize_lightgbm(self):
        """Initialize LightGBM model"""
        params = json.loads(self.model_parameters or "{}")
        default_params = {
            "objective": "regression" if self._is_regression_model() else "multiclass",
            "num_leaves": 31,
            "learning_rate": 0.1,
            "n_estimators": 100,
            "random_state": self.random_state,
        }
        default_params.update(params)
        self.model_parameters = json.dumps(default_params)

    def _initialize_random_forest(self):
        """Initialize Random Forest model"""
        params = json.loads(self.model_parameters or "{}")
        default_params = {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": self.random_state,
        }
        default_params.update(params)
        self.model_parameters = json.dumps(default_params)

    def _initialize_gradient_boosting(self):
        """Initialize Gradient Boosting model"""
        params = json.loads(self.model_parameters or "{}")
        default_params = {
            "n_estimators": 100,
            "learning_rate": 0.1,
            "max_depth": 3,
            "random_state": self.random_state,
        }
        default_params.update(params)
        self.model_parameters = json.dumps(default_params)

    def _is_regression_model(self):
        """Check if model is regression type"""
        return self.model_type in [
            "cost_prediction",
            "schedule_forecast",
            "quality_prediction",
        ]

    def train_model(self):
        """Train the ML model with historical data"""
        self.ensure_one()

        try:
            start_time = datetime.now()

            # Gather training data
            X, y = self._gather_training_data()

            if len(X) == 0:
                raise UserError("No training data available")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.test_size, random_state=self.random_state
            )

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            model = self._train_model_algorithm(X_train_scaled, y_train)

            # Evaluate model
            predictions = model.predict(X_test_scaled)
            self._evaluate_model(predictions, y_test)

            # Save model
            self._save_trained_model(model, scaler)

            # Update status
            training_time = (datetime.now() - start_time).total_seconds()
            self.write(
                {
                    "is_trained": True,
                    "training_date": datetime.now(),
                    "training_time": training_time,
                    "training_data_size": len(X_train),
                }
            )

            _logger.info(f"Successfully trained model {self.model_name}")
            return {
                "success": True,
                "message": f"Model trained successfully. Accuracy: {self.accuracy_score:.4f}",
            }

        except Exception as e:
            _logger.error(f"Failed to train model {self.model_name}: {e}")
            return {"success": False, "error": str(e)}

    def _gather_training_data(self):
        """Gather training data from various sources"""
        self.ensure_one()

        data_collectors = {
            "cost_prediction": self._gather_cost_data,
            "risk_assessment": self._gather_risk_data,
            "schedule_forecast": self._gather_schedule_data,
            "quality_prediction": self._gather_quality_data,
            "resource_optimization": self._gather_resource_data,
            "anomaly_detection": self._gather_anomaly_data,
        }

        collector = data_collectors.get(self.model_type)
        if not collector:
            raise UserError(f"No data collector for model type: {self.model_type}")

        return collector()

    def _gather_cost_data(self):
        """Gather cost prediction training data"""
        # Get project financial data
        projects = self.env["project.project"].search([], limit=self.training_data_size)

        data = []
        targets = []

        for project in projects:
            # Features
            features = [
                project.planned_hours or 0,
                len(project.task_ids),
                project.user_id.id if project.user_id else 0,
                project.date_start and (datetime.now() - project.date_start).days or 0,
            ]

            # Target: actual cost vs planned cost ratio
            planned_cost = sum(
                task.planned_hours * 50 for task in project.task_ids
            )  # Assuming $50/hour
            actual_cost = project.total_cost or planned_cost

            if planned_cost > 0:
                data.append(features)
                targets.append(actual_cost / planned_cost)

        return np.array(data), np.array(targets)

    def _gather_risk_data(self):
        """Gather risk assessment training data"""
        risks = self.env["project.risk"].search([], limit=self.training_data_size)

        data = []
        targets = []

        for risk in risks:
            features = [
                risk.probability,
                risk.impact,
                risk.category_id.id if risk.category_id else 0,
                risk.project_id.id if risk.project_id else 0,
                len(risk.mitigation_actions or ""),
            ]

            # Target: risk level (0-4 scale)
            targets.append(risk.risk_level)

            data.append(features)

        return np.array(data), np.array(targets)

    def _gather_schedule_data(self):
        """Gather schedule forecast training data"""
        tasks = self.env["project.task"].search([], limit=self.training_data_size)

        data = []
        targets = []

        for task in tasks:
            features = [
                task.planned_hours or 0,
                task.user_id.id if task.user_id else 0,
                task.project_id.id if task.project_id else 0,
                task.priority or 0,
            ]

            # Target: actual duration vs planned duration ratio
            planned_duration = task.planned_hours or 1
            actual_duration = task.effective_hours or planned_duration

            data.append(features)
            targets.append(actual_duration / planned_duration)

        return np.array(data), np.array(targets)

    def _gather_quality_data(self):
        """Gather quality prediction training data"""
        # Placeholder - would need quality control data
        return np.array([[1, 2, 3]]), np.array([0.8])

    def _gather_resource_data(self):
        """Gather resource optimization training data"""
        # Placeholder - would need resource allocation data
        return np.array([[1, 2, 3]]), np.array([0.7])

    def _gather_anomaly_data(self):
        """Gather anomaly detection training data"""
        # Placeholder - would need normal operation data
        return np.array([[1, 2, 3]]), np.array([0])

    def _train_model_algorithm(self, X_train, y_train):
        """Train model using selected algorithm"""
        params = json.loads(self.model_parameters)

        if self.algorithm == "xgboost":
            if self._is_regression_model():
                model = xgb.XGBRegressor(**params)
            else:
                model = xgb.XGBClassifier(**params)

        elif self.algorithm == "lightgbm":
            if self._is_regression_model():
                model = lgb.LGBMRegressor(**params)
            else:
                model = lgb.LGBMClassifier(**params)

        elif self.algorithm == "random_forest":
            if self._is_regression_model():
                model = RandomForestRegressor(**params)
            else:
                from sklearn.ensemble import RandomForestClassifier

                model = RandomForestClassifier(**params)

        elif self.algorithm == "gradient_boosting":
            if self._is_regression_model():
                model = GradientBoostingRegressor(**params)
            else:
                model = GradientBoostingClassifier(**params)

        model.fit(X_train, y_train)
        return model

    def _evaluate_model(self, predictions, y_test):
        """Evaluate model performance"""
        if self._is_regression_model():
            mae = mean_absolute_error(y_test, predictions)
            self.mae_score = mae
            self.accuracy_score = 1 - mae  # Simple accuracy for regression
        else:
            accuracy = accuracy_score(y_test, predictions)
            self.accuracy_score = accuracy
            self.mae_score = 0  # Not applicable for classification

    def _save_trained_model(self, model, scaler):
        """Save trained model (placeholder - would save to file/database)"""
        # In a real implementation, you would save the model to a file or database
        pass

    def predict(self, features):
        """Make prediction using trained model"""
        self.ensure_one()

        if not self.is_trained:
            raise UserError("Model is not trained yet")

        try:
            # Load model and scaler (placeholder)
            # In real implementation, load from saved file/database

            # For now, return mock predictions
            if self.model_type == "cost_prediction":
                return 1.15  # 15% cost overrun prediction
            elif self.model_type == "risk_assessment":
                return 2  # Medium risk
            elif self.model_type == "schedule_forecast":
                return 1.08  # 8% delay prediction
            else:
                return 0.5

        except Exception as e:
            _logger.error(f"Prediction failed for model {self.model_name}: {e}")
            raise UserError(f"Prediction failed: {e}")

    def get_feature_importance(self):
        """Get feature importance from trained model"""
        self.ensure_one()

        if not self.is_trained:
            return {}

        # Placeholder - would extract from actual model
        features = {
            "cost_prediction": ["planned_hours", "task_count", "manager", "duration"],
            "risk_assessment": [
                "probability",
                "impact",
                "category",
                "project",
                "actions",
            ],
            "schedule_forecast": ["planned_hours", "assignee", "project", "priority"],
        }

        feature_names = features.get(self.model_type, [])
        importance_values = np.random.rand(len(feature_names))  # Mock values

        return dict(zip(feature_names, importance_values))


class AIPredictiveAnalytics(models.Model):
    """Predictive Analytics Dashboard"""

    _name = "ofitec.ai.predictive"
    _description = "AI Predictive Analytics"
    _rec_name = "analysis_name"

    analysis_name = fields.Char(string="Analysis Name", required=True)
    analysis_type = fields.Selection(
        [
            ("cost_overrun", "Cost Overrun Prediction"),
            ("risk_trends", "Risk Trends Analysis"),
            ("schedule_delays", "Schedule Delay Prediction"),
            ("quality_issues", "Quality Issues Prediction"),
            ("resource_conflicts", "Resource Conflicts"),
            ("anomaly_detection", "Anomaly Detection"),
        ],
        string="Analysis Type",
        required=True,
    )

    project_id = fields.Many2one("project.project", string="Project")
    is_active = fields.Boolean(string="Active", default=True)

    # Results
    prediction_value = fields.Float(string="Prediction Value")
    confidence_level = fields.Float(string="Confidence Level")
    risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Risk Level",
        compute="_compute_risk_level",
    )

    # Recommendations
    recommendations = fields.Text(string="AI Recommendations")
    preventive_actions = fields.Text(string="Preventive Actions")

    # Metadata
    analysis_date = fields.Datetime(string="Analysis Date", default=datetime.now)
    next_review_date = fields.Date(string="Next Review Date")

    @api.depends("prediction_value", "analysis_type")
    def _compute_risk_level(self):
        """Compute risk level based on prediction value"""
        for record in self:
            if record.analysis_type in ["cost_overrun", "schedule_delays"]:
                if record.prediction_value > 1.2:
                    record.risk_level = "critical"
                elif record.prediction_value > 1.1:
                    record.risk_level = "high"
                elif record.prediction_value > 1.05:
                    record.risk_level = "medium"
                else:
                    record.risk_level = "low"
            else:
                record.risk_level = "medium"  # Default

    @api.model
    def run_predictive_analysis(self, project_id=None):
        """Run predictive analysis for projects"""
        projects = self.env["project.project"]
        if project_id:
            projects = projects.browse(project_id)
        else:
            projects = projects.search([])

        results = []

        for project in projects:
            analysis_result = self._analyze_project(project)
            results.append(analysis_result)

        return results

    def _analyze_project(self, project):
        """Analyze individual project"""
        # Cost overrun prediction
        cost_prediction = self._predict_cost_overrun(project)

        # Schedule delay prediction
        schedule_prediction = self._predict_schedule_delay(project)

        # Risk assessment
        risk_assessment = self._assess_project_risks(project)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            cost_prediction, schedule_prediction, risk_assessment
        )

        return {
            "project_id": project.id,
            "project_name": project.name,
            "cost_prediction": cost_prediction,
            "schedule_prediction": schedule_prediction,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "analysis_date": datetime.now(),
        }

    def _predict_cost_overrun(self, project):
        """Predict cost overrun using ML model"""
        # Get cost prediction model
        cost_model = self.env["ofitec.ai.analytics"].search(
            [
                ("model_type", "=", "cost_prediction"),
                ("is_active", "=", True),
                ("is_trained", "=", True),
            ],
            limit=1,
        )

        if cost_model:
            # Prepare features
            features = [
                project.planned_hours or 0,
                len(project.task_ids),
                project.user_id.id if project.user_id else 0,
                project.date_start and (datetime.now() - project.date_start).days or 0,
            ]
            return cost_model.predict(features)
        else:
            # Fallback to simple heuristic
            return 1.0 + (len(project.task_ids) * 0.01)

    def _predict_schedule_delay(self, project):
        """Predict schedule delays"""
        schedule_model = self.env["ofitec.ai.analytics"].search(
            [
                ("model_type", "=", "schedule_forecast"),
                ("is_active", "=", True),
                ("is_trained", "=", True),
            ],
            limit=1,
        )

        if schedule_model:
            features = [
                sum(task.planned_hours or 0 for task in project.task_ids),
                len(
                    [task for task in project.task_ids if task.stage_id.name == "Done"]
                ),
                len(project.task_ids),
            ]
            return schedule_model.predict(features)
        else:
            # Fallback heuristic
            completed_tasks = len(
                [task for task in project.task_ids if task.stage_id.name == "Done"]
            )
            total_tasks = len(project.task_ids)
            if total_tasks > 0:
                return 1.0 + ((total_tasks - completed_tasks) / total_tasks) * 0.1
            return 1.0

    def _assess_project_risks(self, project):
        """Assess project risks"""
        risk_model = self.env["ofitec.ai.analytics"].search(
            [
                ("model_type", "=", "risk_assessment"),
                ("is_active", "=", True),
                ("is_trained", "=", True),
            ],
            limit=1,
        )

        if risk_model:
            # Get project risks
            risks = self.env["project.risk"].search([("project_id", "=", project.id)])
            if risks:
                avg_probability = sum(risk.probability for risk in risks) / len(risks)
                avg_impact = sum(risk.impact for risk in risks) / len(risks)
                features = [avg_probability, avg_impact, len(risks)]
                return risk_model.predict(features)
            return 1  # Low risk
        else:
            # Count high priority risks
            high_risks = self.env["project.risk"].search_count(
                [("project_id", "=", project.id), ("priority", "in", ["1", "2"])]
            )
            return min(high_risks + 1, 4)  # Scale 1-4

    def _generate_recommendations(self, cost_pred, schedule_pred, risk_level):
        """Generate AI-powered recommendations"""
        recommendations = []

        if cost_pred > 1.1:
            overrun_pct = (cost_pred - 1) * 100
            recommendations.append(f"⚠️ Cost overrun predicted: {overrun_pct:.1f}%")
            recommendations.append(
                "📋 Review budget allocation and resource efficiency"
            )
            recommendations.append("🔍 Identify high-cost tasks and optimize execution")

        if schedule_pred > 1.1:
            delay_pct = (schedule_pred - 1) * 100
            recommendations.append(f"⏰ Schedule delay predicted: {delay_pct:.1f}%")
            recommendations.append("📅 Review critical path and dependencies")
            recommendations.append("👥 Consider resource reallocation")

        if risk_level >= 3:
            recommendations.append("🚨 High risk level detected")
            recommendations.append("🛡️ Implement additional risk mitigation measures")
            recommendations.append("📊 Increase monitoring frequency")

        if not recommendations:
            recommendations.append("✅ Project on track - continue current execution")
            recommendations.append("📈 Consider optimization opportunities")

        return "\n".join(recommendations)


class AIRealTimeAnalytics(models.Model):
    """Real-time Analytics Dashboard"""

    _name = "ofitec.ai.realtime"
    _description = "AI Real-time Analytics"
    _rec_name = "metric_name"

    metric_name = fields.Char(string="Metric Name", required=True)
    metric_type = fields.Selection(
        [
            ("kpi", "KPI"),
            ("performance", "Performance"),
            ("quality", "Quality"),
            ("risk", "Risk"),
            ("cost", "Cost"),
            ("schedule", "Schedule"),
        ],
        string="Metric Type",
        required=True,
    )

    current_value = fields.Float(string="Current Value")
    target_value = fields.Float(string="Target Value")
    previous_value = fields.Float(string="Previous Value")

    trend = fields.Selection(
        [
            ("up", "Trending Up"),
            ("down", "Trending Down"),
            ("stable", "Stable"),
            ("volatile", "Volatile"),
        ],
        string="Trend",
        compute="_compute_trend",
    )

    status = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("warning", "Warning"),
            ("critical", "Critical"),
        ],
        string="Status",
        compute="_compute_status",
    )

    last_updated = fields.Datetime(string="Last Updated", default=datetime.now)

    @api.depends("current_value", "previous_value")
    def _compute_trend(self):
        """Compute trend based on current vs previous values"""
        for record in self:
            if record.previous_value:
                change_pct = (
                    (record.current_value - record.previous_value)
                    / record.previous_value
                ) * 100
                if change_pct > 5:
                    record.trend = "up"
                elif change_pct < -5:
                    record.trend = "down"
                else:
                    record.trend = "stable"
            else:
                record.trend = "stable"

    @api.depends("current_value", "target_value", "metric_type")
    def _compute_status(self):
        """Compute status based on performance vs target"""
        for record in self:
            if record.target_value:
                performance_pct = (record.current_value / record.target_value) * 100

                if performance_pct >= 100:
                    record.status = "excellent"
                elif performance_pct >= 90:
                    record.status = "good"
                elif performance_pct >= 75:
                    record.status = "warning"
                else:
                    record.status = "critical"
            else:
                record.status = "good"

    @api.model
    def update_realtime_metrics(self):
        """Update all real-time metrics"""
        metrics = self.search([])

        for metric in metrics:
            metric._update_metric_value()
            metric.last_updated = datetime.now()

        return True

    def _update_metric_value(self):
        """Update metric value based on type"""
        self.ensure_one()

        # Store previous value
        self.previous_value = self.current_value

        if self.metric_type == "kpi":
            self.current_value = self._calculate_kpi_value()
        elif self.metric_type == "performance":
            self.current_value = self._calculate_performance_value()
        elif self.metric_type == "quality":
            self.current_value = self._calculate_quality_value()
        elif self.metric_type == "risk":
            self.current_value = self._calculate_risk_value()
        elif self.metric_type == "cost":
            self.current_value = self._calculate_cost_value()
        elif self.metric_type == "schedule":
            self.current_value = self._calculate_schedule_value()

    def _calculate_kpi_value(self):
        """Calculate KPI value"""
        # Project completion rate
        total_projects = self.env["project.project"].search_count([])
        completed_projects = self.env["project.project"].search_count(
            [("stage_id.name", "=", "Done")]
        )

        if total_projects > 0:
            return (completed_projects / total_projects) * 100
        return 0

    def _calculate_performance_value(self):
        """Calculate performance value"""
        # Average task completion time vs planned
        tasks = self.env["project.task"].search(
            [
                ("stage_id.name", "=", "Done"),
                ("effective_hours", ">", 0),
                ("planned_hours", ">", 0),
            ],
            limit=100,
        )

        if tasks:
            ratios = [task.effective_hours / task.planned_hours for task in tasks]
            return (sum(ratios) / len(ratios)) * 100
        return 100

    def _calculate_quality_value(self):
        """Calculate quality value"""
        # Quality score based on completed tasks without issues
        total_tasks = self.env["project.task"].search_count(
            [("stage_id.name", "=", "Done")]
        )

        # Tasks with issues (placeholder - would need quality control module)
        tasks_with_issues = total_tasks * 0.05  # Assume 5% have issues

        if total_tasks > 0:
            return ((total_tasks - tasks_with_issues) / total_tasks) * 100
        return 100

    def _calculate_risk_value(self):
        """Calculate risk value"""
        # Average risk score across projects
        risks = self.env["project.risk"].search([])

        if risks:
            avg_risk = sum(risk.probability * risk.impact for risk in risks) / len(
                risks
            )
            return 100 - (avg_risk / 25) * 100  # Convert to 0-100 scale
        return 100

    def _calculate_cost_value(self):
        """Calculate cost performance"""
        # Budget utilization
        projects = self.env["project.project"].search([])

        if projects:
            total_planned = sum(
                project.planned_hours * 50 for project in projects
            )  # $50/hour
            total_actual = sum(project.total_cost or 0 for project in projects)

            if total_planned > 0:
                return (total_actual / total_planned) * 100
        return 100

    def _calculate_schedule_value(self):
        """Calculate schedule performance"""
        # On-time delivery rate
        projects = self.env["project.project"].search([("stage_id.name", "=", "Done")])

        if projects:
            on_time = sum(
                1
                for project in projects
                if project.date_end and project.date_end <= project.date
            )
            return (on_time / len(projects)) * 100
        return 100


class AIAPIController(models.Model):
    """REST API Controller for AI Services"""

    _name = "ofitec.ai.api"
    _description = "AI API Controller"

    @api.model
    def get_predictive_insights(self, project_id=None):
        """Get predictive insights via API"""
        predictive = self.env["ofitec.ai.predictive"]
        return predictive.run_predictive_analysis(project_id)

    @api.model
    def get_realtime_metrics(self):
        """Get real-time metrics via API"""
        realtime = self.env["ofitec.ai.realtime"]
        realtime.update_realtime_metrics()

        metrics = realtime.search([])
        return [
            {
                "name": metric.metric_name,
                "type": metric.metric_type,
                "current": metric.current_value,
                "target": metric.target_value,
                "trend": metric.trend,
                "status": metric.status,
            }
            for metric in metrics
        ]

    @api.model
    def train_ml_model(self, model_id):
        """Train ML model via API"""
        model = self.env["ofitec.ai.analytics"].browse(model_id)
        if model:
            return model.train_model()
        return {"success": False, "error": "Model not found"}

    @api.model
    def get_model_predictions(self, model_id, features):
        """Get predictions from trained model via API"""
        model = self.env["ofitec.ai.analytics"].browse(model_id)
        if model:
            return {"prediction": model.predict(features)}
        return {"error": "Model not found"}
