# -*- coding: utf-8 -*-
"""
Horizontal Scaling Configuration for Advanced AI Module
Implements Redis caching, load balancing, and monitoring capabilities
"""

try:
    import redis
except ImportError:  # Optional dependency; module should still load without Redis
    redis = None
import json
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIScalingConfiguration(models.Model):
    """Configuration for horizontal scaling"""

    _name = "ofitec.ai.scaling"
    _description = "AI Horizontal Scaling Configuration"
    _rec_name = "scaling_name"

    scaling_name = fields.Char(string="Scaling Configuration", required=True)
    is_active = fields.Boolean(string="Active", default=True)

    # Redis Configuration
    redis_host = fields.Char(string="Redis Host", default="redis", required=True)
    redis_port = fields.Integer(string="Redis Port", default=6379, required=True)
    redis_db = fields.Integer(string="Redis Database", default=0)
    redis_password = fields.Char(string="Redis Password")
    redis_ssl = fields.Boolean(string="Redis SSL", default=False)

    # Cache Configuration
    cache_ttl = fields.Integer(
        string="Cache TTL (seconds)", default=3600, help="Time to live for cached data"
    )
    max_cache_size = fields.Integer(string="Max Cache Size (MB)", default=512)

    # Load Balancing
    enable_load_balancing = fields.Boolean(
        string="Enable Load Balancing", default=False
    )
    worker_nodes = fields.Text(
        string="Worker Nodes", help="JSON list of worker node URLs"
    )
    load_balancing_strategy = fields.Selection(
        [
            ("round_robin", "Round Robin"),
            ("least_loaded", "Least Loaded"),
            ("weighted", "Weighted"),
            ("ip_hash", "IP Hash"),
        ],
        string="Load Balancing Strategy",
        default="round_robin",
    )

    # Monitoring
    enable_monitoring = fields.Boolean(string="Enable Monitoring", default=True)
    monitoring_interval = fields.Integer(
        string="Monitoring Interval (seconds)", default=60
    )
    alert_threshold_cpu = fields.Float(string="CPU Alert Threshold (%)", default=80.0)
    alert_threshold_memory = fields.Float(
        string="Memory Alert Threshold (%)", default=85.0
    )
    alert_threshold_response_time = fields.Float(
        string="Response Time Alert Threshold (ms)", default=1000.0
    )

    # Auto-scaling
    enable_auto_scaling = fields.Boolean(string="Enable Auto-scaling", default=False)
    min_workers = fields.Integer(string="Minimum Workers", default=2)
    max_workers = fields.Integer(string="Maximum Workers", default=10)
    scale_up_threshold = fields.Float(string="Scale Up Threshold (%)", default=75.0)
    scale_down_threshold = fields.Float(string="Scale Down Threshold (%)", default=25.0)

    # Performance Metrics
    last_health_check = fields.Datetime(string="Last Health Check")
    active_workers = fields.Integer(string="Active Workers", readonly=True)
    avg_response_time = fields.Float(string="Avg Response Time (ms)", readonly=True)
    cache_hit_rate = fields.Float(string="Cache Hit Rate (%)", readonly=True)

    def get_redis_connection(self):
        """Get Redis connection"""
        self.ensure_one()

        try:
            if redis is None:
                raise UserError(
                    "Python package 'redis' no está instalado en el servidor de Odoo"
                )
            connection_params = {
                "host": self.redis_host,
                "port": self.redis_port,
                "db": self.redis_db,
                "decode_responses": True,
            }

            if self.redis_password:
                connection_params["password"] = self.redis_password

            if self.redis_ssl:
                connection_params["ssl"] = True

            return redis.Redis(**connection_params)

        except Exception as e:
            _logger.error(f"Failed to connect to Redis: {e}")
            raise UserError(f"Redis connection failed: {e}")

    def test_redis_connection(self):
        """Test Redis connection"""
        self.ensure_one()

        try:
            r = self.get_redis_connection()
            r.ping()
            return {"success": True, "message": "Redis connection successful"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def cache_set(self, key, value, ttl=None):
        """Set value in cache"""
        self.ensure_one()

        try:
            r = self.get_redis_connection()
            ttl_value = ttl or self.cache_ttl

            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            return r.setex(key, ttl_value, value)

        except Exception as e:
            _logger.error(f"Cache set failed for key {key}: {e}")
            return False

    def cache_get(self, key):
        """Get value from cache"""
        self.ensure_one()

        try:
            r = self.get_redis_connection()
            value = r.get(key)

            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value

            return None

        except Exception as e:
            _logger.error(f"Cache get failed for key {key}: {e}")
            return None

    def cache_delete(self, key):
        """Delete value from cache"""
        self.ensure_one()

        try:
            r = self.get_redis_connection()
            return r.delete(key)
        except Exception as e:
            _logger.error(f"Cache delete failed for key {key}: {e}")
            return False

    def cache_clear(self):
        """Clear all cache"""
        self.ensure_one()

        try:
            r = self.get_redis_connection()
            return r.flushdb()
        except Exception as e:
            _logger.error(f"Cache clear failed: {e}")
            return False

    def get_cache_stats(self):
        """Get cache statistics"""
        self.ensure_one()

        try:
            r = self.get_redis_connection()
            info = r.info()

            return {
                "used_memory": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_connections_received": info.get("total_connections_received", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
            }

        except Exception as e:
            _logger.error(f"Failed to get cache stats: {e}")
            return {}

    def _calculate_hit_rate(self, info):
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total > 0:
            return (hits / total) * 100
        return 0

    def distribute_load(self, task_data):
        """Distribute task to worker nodes"""
        self.ensure_one()

        if not self.enable_load_balancing:
            return self._execute_task_locally(task_data)

        try:
            worker_nodes = json.loads(self.worker_nodes or "[]")

            if not worker_nodes:
                return self._execute_task_locally(task_data)

            # Select worker based on strategy
            worker_url = self._select_worker(worker_nodes)

            # Send task to worker
            return self._send_task_to_worker(worker_url, task_data)

        except Exception as e:
            _logger.error(f"Load distribution failed: {e}")
            return self._execute_task_locally(task_data)

    def _select_worker(self, worker_nodes):
        """Select worker based on load balancing strategy"""
        if self.load_balancing_strategy == "round_robin":
            return self._round_robin_selection(worker_nodes)
        elif self.load_balancing_strategy == "least_loaded":
            return self._least_loaded_selection(worker_nodes)
        elif self.load_balancing_strategy == "weighted":
            return self._weighted_selection(worker_nodes)
        elif self.load_balancing_strategy == "ip_hash":
            return self._ip_hash_selection(worker_nodes)
        else:
            return worker_nodes[0]  # Default to first worker

    def _round_robin_selection(self, worker_nodes):
        """Round-robin worker selection"""
        # Simple implementation - in production use consistent hashing
        current_index = getattr(self, "_rr_index", 0)
        selected_worker = worker_nodes[current_index]
        self._rr_index = (current_index + 1) % len(worker_nodes)
        return selected_worker

    def _least_loaded_selection(self, worker_nodes):
        """Select least loaded worker"""
        # Check worker loads (simplified - check response times)
        worker_loads = {}
        for worker in worker_nodes:
            load = self._get_worker_load(worker)
            worker_loads[worker] = load

        return min(worker_loads, key=worker_loads.get)

    def _weighted_selection(self, worker_nodes):
        """Weighted worker selection"""
        # Simplified - equal weights for now
        return self._round_robin_selection(worker_nodes)

    def _ip_hash_selection(self, worker_nodes):
        """IP hash-based selection"""
        import hashlib

        # Get client IP (simplified)
        client_ip = self.env.context.get("client_ip", "127.0.0.1")

        # Hash IP to select worker
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        worker_index = hash_value % len(worker_nodes)

        return worker_nodes[worker_index]

    def _get_worker_load(self, worker_url):
        """Get worker load (simplified implementation)"""
        try:
            # In production, this would query worker health endpoint
            # For now, return random load
            import random

            return random.uniform(0, 100)
        except Exception:
            return 100  # High load if unable to determine

    def _send_task_to_worker(self, worker_url, task_data):
        """Send task to worker node"""
        import requests

        try:
            response = requests.post(
                f"{worker_url}/api/v1/ai/worker/execute", json=task_data, timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Worker returned status {response.status_code}")

        except Exception as e:
            _logger.error(f"Failed to send task to worker {worker_url}: {e}")
            raise

    def _execute_task_locally(self, task_data):
        """Execute task locally"""
        # Execute AI task locally
        task_type = task_data.get("type")

        if task_type == "prediction":
            return self._execute_prediction_task(task_data)
        elif task_type == "training":
            return self._execute_training_task(task_data)
        elif task_type == "analytics":
            return self._execute_analytics_task(task_data)
        else:
            raise UserError(f"Unknown task type: {task_type}")

    def _execute_prediction_task(self, task_data):
        """Execute prediction task"""
        model_id = task_data.get("model_id")
        features = task_data.get("features", [])

        model = self.env["ofitec.ai.analytics"].browse(model_id)
        if model:
            prediction = model.predict(features)
            return {"prediction": prediction}
        else:
            raise UserError("Model not found")

    def _execute_training_task(self, task_data):
        """Execute training task"""
        model_id = task_data.get("model_id")

        model = self.env["ofitec.ai.analytics"].browse(model_id)
        if model:
            return model.train_model()
        else:
            raise UserError("Model not found")

    def _execute_analytics_task(self, task_data):
        """Execute analytics task"""
        project_id = task_data.get("project_id")

        predictive = self.env["ofitec.ai.predictive"]
        return predictive.run_predictive_analysis(project_id)

    def perform_health_check(self):
        """Perform health check on scaling infrastructure"""
        self.ensure_one()

        health_status = {
            "redis_connected": False,
            "workers_healthy": 0,
            "total_workers": 0,
            "cache_performance": {},
            "timestamp": datetime.now().isoformat(),
        }

        # Check Redis connection
        try:
            r = self.get_redis_connection()
            r.ping()
            health_status["redis_connected"] = True
            health_status["cache_performance"] = self.get_cache_stats()
        except Exception as e:
            _logger.error(f"Redis health check failed: {e}")

        # Check worker nodes
        if self.enable_load_balancing and self.worker_nodes:
            try:
                worker_nodes = json.loads(self.worker_nodes)
                health_status["total_workers"] = len(worker_nodes)

                for worker in worker_nodes:
                    if self._check_worker_health(worker):
                        health_status["workers_healthy"] += 1

            except Exception as e:
                _logger.error(f"Worker health check failed: {e}")

        # Update metrics
        self.write(
            {
                "last_health_check": datetime.now(),
                "active_workers": health_status["workers_healthy"],
            }
        )

        return health_status

    def _check_worker_health(self, worker_url):
        """Check worker node health"""
        import requests

        try:
            response = requests.get(f"{worker_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_performance_metrics(self):
        """Get performance metrics"""
        self.ensure_one()

        # Get cache performance
        cache_stats = self.get_cache_stats()

        # Calculate response times (simplified)
        # In production, this would track actual response times
        avg_response_time = 150.0  # Mock value

        # Update metrics
        self.write(
            {
                "avg_response_time": avg_response_time,
                "cache_hit_rate": cache_stats.get("hit_rate", 0),
            }
        )

        return {
            "cache_stats": cache_stats,
            "avg_response_time": avg_response_time,
            "active_workers": self.active_workers,
            "last_health_check": self.last_health_check,
        }

    def scale_workers(self, direction):
        """Scale workers up or down"""
        self.ensure_one()

        if not self.enable_auto_scaling:
            return {"success": False, "message": "Auto-scaling not enabled"}

        try:
            if direction == "up":
                new_worker_count = min(self.active_workers + 1, self.max_workers)
            elif direction == "down":
                new_worker_count = max(self.active_workers - 1, self.min_workers)
            else:
                return {"success": False, "message": "Invalid direction"}

            # In production, this would interact with container orchestration
            # For now, just update the count
            self.write({"active_workers": new_worker_count})

            return {
                "success": True,
                "message": f"Scaled to {new_worker_count} workers",
                "worker_count": new_worker_count,
            }

        except Exception as e:
            _logger.error(f"Scaling failed: {e}")
            return {"success": False, "message": str(e)}

    def monitor_system(self):
        """Monitor system performance and trigger alerts"""
        self.ensure_one()

        if not self.enable_monitoring:
            return

        try:
            # Get current metrics
            metrics = self.get_performance_metrics()

            alerts = []

            # Check CPU threshold
            if metrics.get("cpu_usage", 0) > self.alert_threshold_cpu:
                alerts.append(
                    {
                        "type": "cpu",
                        "message": (
                            f'CPU usage ({metrics["cpu_usage"]}%) exceeds threshold '
                            f'({self.alert_threshold_cpu}%)'
                        ),
                    }
                )

            # Check memory threshold
            if metrics.get("memory_usage", 0) > self.alert_threshold_memory:
                alerts.append(
                    {
                        "type": "memory",
                        "message": (
                            f'Memory usage ({metrics["memory_usage"]}%) exceeds threshold '
                            f'({self.alert_threshold_memory}%)'
                        ),
                    }
                )

            # Check response time threshold
            if self.avg_response_time > self.alert_threshold_response_time:
                alerts.append(
                    {
                        "type": "response_time",
                        "message": (
                            f"Response time ({self.avg_response_time}ms) exceeds threshold "
                            f"({self.alert_threshold_response_time}ms)"
                        ),
                    }
                )

            # Send alerts
            for alert in alerts:
                self._send_alert(alert)

            # Auto-scaling logic
            if self.enable_auto_scaling:
                self._check_auto_scaling(metrics)

        except Exception as e:
            _logger.error(f"Monitoring failed: {e}")

    def _send_alert(self, alert):
        """Send alert notification"""
        # Create notification in Odoo
        self.env["mail.message"].create(
            {
                "subject": f"AI System Alert: {alert['type'].upper()}",
                "body": alert["message"],
                "message_type": "notification",
                "subtype_id": self.env.ref("mail.mt_note").id,
            }
        )

        # Send to Slack if configured
        webhook_config = self.env["ofitec.ai.webhook_security"].search(
            [("service", "=", "slack"), ("is_active", "=", True)], limit=1
        )

        if webhook_config:
            self._send_slack_alert(webhook_config, alert)

    def _send_slack_alert(self, webhook_config, alert):
        """Send alert to Slack"""
        import requests

        try:
            message = {
                "text": f"🚨 AI System Alert: {alert['type'].upper()}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{alert['type'].upper()} Alert*\n{alert['message']}",
                        },
                    }
                ],
            }

            requests.post(webhook_config.webhook_url, json=message, timeout=10)

        except Exception as e:
            _logger.error(f"Slack alert failed: {e}")

    def _check_auto_scaling(self, metrics):
        """Check if auto-scaling is needed"""
        cpu_usage = metrics.get("cpu_usage", 0)

        if (
            cpu_usage > self.scale_up_threshold
            and self.active_workers < self.max_workers
        ):
            self.scale_workers("up")
        elif (
            cpu_usage < self.scale_down_threshold
            and self.active_workers > self.min_workers
        ):
            self.scale_workers("down")


class AIMonitoringDashboard(models.Model):
    """Monitoring dashboard for AI system"""

    _name = "ofitec.ai.monitoring"
    _description = "AI System Monitoring Dashboard"
    _rec_name = "metric_name"

    metric_name = fields.Char(string="Metric Name", required=True)
    metric_type = fields.Selection(
        [
            ("performance", "Performance"),
            ("system", "System"),
            ("cache", "Cache"),
            ("worker", "Worker"),
            ("prediction", "Prediction"),
            ("training", "Training"),
        ],
        string="Metric Type",
        required=True,
    )

    current_value = fields.Float(string="Current Value")
    previous_value = fields.Float(string="Previous Value")
    unit = fields.Char(string="Unit", default="%")
    timestamp = fields.Datetime(string="Timestamp", default=datetime.now)

    # Thresholds
    warning_threshold = fields.Float(string="Warning Threshold")
    critical_threshold = fields.Float(string="Critical Threshold")

    # Status
    status = fields.Selection(
        [("normal", "Normal"), ("warning", "Warning"), ("critical", "Critical")],
        string="Status",
        compute="_compute_status",
    )

    @api.depends("current_value", "warning_threshold", "critical_threshold")
    def _compute_status(self):
        """Compute status based on thresholds"""
        for record in self:
            if (
                record.critical_threshold
                and record.current_value >= record.critical_threshold
            ):
                record.status = "critical"
            elif (
                record.warning_threshold
                and record.current_value >= record.warning_threshold
            ):
                record.status = "warning"
            else:
                record.status = "normal"

    @api.model
    def collect_metrics(self):
        """Collect all monitoring metrics"""
        # Get scaling configuration
        scaling_config = self.env["ofitec.ai.scaling"].search(
            [("is_active", "=", True)], limit=1
        )

        if scaling_config:
            # Collect cache metrics
            cache_stats = scaling_config.get_cache_stats()
            self._store_metric(
                "cache_hit_rate", cache_stats.get("hit_rate", 0), "%", 80, 90
            )

            # Collect performance metrics
            perf_metrics = scaling_config.get_performance_metrics()
            self._store_metric(
                "avg_response_time",
                perf_metrics.get("avg_response_time", 0),
                "ms",
                500,
                1000,
            )
            self._store_metric(
                "active_workers", scaling_config.active_workers, "count", 1, 0
            )

        # Collect AI model metrics
        ai_models = self.env["ofitec.ai.analytics"].search([("is_active", "=", True)])
        for model in ai_models:
            self._store_metric(
                f"{model.model_name}_accuracy", model.accuracy_score * 100, "%", 70, 85
            )

        # Collect prediction metrics
        predictive_analytics = self.env["ofitec.ai.predictive"].search(
            [("is_active", "=", True)], limit=10
        )

        if predictive_analytics:
            avg_confidence = sum(
                pa.confidence_level for pa in predictive_analytics
            ) / len(predictive_analytics)
            self._store_metric(
                "avg_prediction_confidence", avg_confidence * 100, "%", 60, 80
            )

    def _store_metric(
        self, name, value, unit, warning_threshold=None, critical_threshold=None
    ):
        """Store a metric value"""
        # Get or create metric record
        metric = self.search(
            [
                ("metric_name", "=", name),
                ("metric_type", "=", self._get_metric_type_from_name(name)),
            ],
            limit=1,
        )

        if not metric:
            metric = self.create(
                {
                    "metric_name": name,
                    "metric_type": self._get_metric_type_from_name(name),
                    "unit": unit,
                    "warning_threshold": warning_threshold,
                    "critical_threshold": critical_threshold,
                }
            )

        # Update values
        metric.write(
            {
                "previous_value": metric.current_value,
                "current_value": value,
                "timestamp": datetime.now(),
            }
        )

    def _get_metric_type_from_name(self, name):
        """Determine metric type from name"""
        if "cache" in name.lower():
            return "cache"
        elif "response" in name.lower() or "prediction" in name.lower():
            return "performance"
        elif "worker" in name.lower():
            return "worker"
        elif "accuracy" in name.lower():
            return "training"
        else:
            return "system"
