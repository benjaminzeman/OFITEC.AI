/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Chart } from "chart.js/auto";

export class AIDashboard extends Component {
    static template = "ofitec_ai_advanced.AIDashboard";

    setup() {
        this.state = useState({
            realtimeMetrics: [],
            predictiveInsights: [],
            mlModels: [],
            selectedProject: null,
            selectedModel: null,
            modelFeatures: null,
            isLoading: false
        });

        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.notification = useService("notification");

        onWillStart(() => {
            this.loadDashboardData();
        });

        onMounted(() => {
            this.initializeCharts();
        });
    }

    async loadDashboardData() {
        this.state.isLoading = true;

        try {
            // Load real-time metrics
            await this.loadRealtimeMetrics();

            // Load predictive insights
            await this.loadPredictiveInsights();

            // Load ML models
            await this.loadMLModels();

        } catch (error) {
            this.notification.add("Error loading dashboard data", {
                type: "danger",
                title: "Dashboard Error"
            });
            console.error("Dashboard load error:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async loadRealtimeMetrics() {
        try {
            const result = await this.rpc("/api/v1/ai/analytics/realtime", {});
            if (result.status === "success") {
                this.state.realtimeMetrics = result.data.metrics;
            }
        } catch (error) {
            console.error("Error loading real-time metrics:", error);
        }
    }

    async loadPredictiveInsights() {
        try {
            const result = await this.rpc("/api/v1/ai/analytics/predictive", {});
            if (result.status === "success") {
                this.state.predictiveInsights = result.data.results;
            }
        } catch (error) {
            console.error("Error loading predictive insights:", error);
        }
    }

    async loadMLModels() {
        try {
            const result = await this.rpc("/api/v1/ai/models", {});
            if (result.status === "success") {
                this.state.mlModels = result.data.models;
            }
        } catch (error) {
            console.error("Error loading ML models:", error);
        }
    }

    async refreshDashboard() {
        await this.loadDashboardData();
        this.updateCharts();
        this.notification.add("Dashboard refreshed successfully", {
            type: "success"
        });
    }

    async trainModel(modelId) {
        try {
            const result = await this.rpc(`/api/v1/ai/models/${modelId}/train`, {}, { method: "POST" });

            if (result.status === "success") {
                this.notification.add("Model training completed successfully", {
                    type: "success",
                    title: "Training Complete"
                });
                await this.loadMLModels(); // Refresh models list
            } else {
                this.notification.add(result.error || "Training failed", {
                    type: "danger",
                    title: "Training Error"
                });
            }
        } catch (error) {
            this.notification.add("Error training model", {
                type: "danger",
                title: "Training Error"
            });
            console.error("Training error:", error);
        }
    }

    async showModelDetails(model) {
        this.state.selectedModel = model;

        try {
            const result = await this.rpc(`/api/v1/ai/models/${model.id}/features`, {});
            if (result.status === "success") {
                this.state.modelFeatures = result.data.features;
            }
        } catch (error) {
            console.error("Error loading model features:", error);
            this.state.modelFeatures = null;
        }

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('modelDetailsModal'));
        modal.show();
    }

    showProjectDetails(insight) {
        this.state.selectedProject = insight;
    }

    async exportData() {
        try {
            const data = {
                realtimeMetrics: this.state.realtimeMetrics,
                predictiveInsights: this.state.predictiveInsights,
                mlModels: this.state.mlModels,
                exportDate: new Date().toISOString()
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ai_dashboard_export_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.notification.add("Data exported successfully", {
                type: "success"
            });
        } catch (error) {
            this.notification.add("Error exporting data", {
                type: "danger"
            });
            console.error("Export error:", error);
        }
    }

    initializeCharts() {
        this.initializePerformanceChart();
        this.initializeRiskChart();
    }

    initializePerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Performance Score',
                    data: [85, 88, 82, 90, 87, 92],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    initializeRiskChart() {
        const ctx = document.getElementById('riskChart');
        if (!ctx) return;

        this.riskChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical'],
                datasets: [{
                    data: [45, 30, 15, 10],
                    backgroundColor: [
                        'rgb(40, 167, 69)',
                        'rgb(255, 193, 7)',
                        'rgb(255, 87, 34)',
                        'rgb(220, 53, 69)'
                    ]
                }]
            },
            options: {
                responsive: true
            }
        });
    }

    updateCharts() {
        if (this.performanceChart) {
            // Update with real data
            this.performanceChart.update();
        }
        if (this.riskChart) {
            // Update with real data
            this.riskChart.update();
        }
    }

    // Utility methods for styling and formatting
    getMetricCardClass(metric) {
        const baseClass = "metric-card";
        const statusClass = this.getStatusClass(metric.status);
        return `${baseClass} ${statusClass}`;
    }

    getStatusClass(status) {
        const classes = {
            'excellent': 'border-success',
            'good': 'border-info',
            'warning': 'border-warning',
            'critical': 'border-danger'
        };
        return classes[status] || 'border-secondary';
    }

    getMetricIcon(type) {
        const icons = {
            'kpi': 'fa-trophy',
            'performance': 'fa-chart-line',
            'quality': 'fa-check-circle',
            'risk': 'fa-exclamation-triangle',
            'cost': 'fa-dollar-sign',
            'schedule': 'fa-calendar'
        };
        return `fa ${icons[type] || 'fa-chart-bar'}`;
    }

    getStatusBadgeClass(status) {
        const classes = {
            'excellent': 'badge bg-success',
            'good': 'badge bg-info',
            'warning': 'badge bg-warning',
            'critical': 'badge bg-danger'
        };
        return classes[status] || 'badge bg-secondary';
    }

    getTrendIcon(trend) {
        const icons = {
            'up': 'fa-arrow-up text-success',
            'down': 'fa-arrow-down text-danger',
            'stable': 'fa-minus text-muted',
            'volatile': 'fa-arrows-alt text-warning'
        };
        return `fa ${icons[trend] || 'fa-minus text-muted'}`;
    }

    getPredictionClass(value) {
        if (value > 1.1) return 'text-danger fw-bold';
        if (value > 1.05) return 'text-warning fw-bold';
        return 'text-success fw-bold';
    }

    getRiskBadgeClass(level) {
        if (level >= 4) return 'badge bg-danger';
        if (level >= 3) return 'badge bg-warning';
        if (level >= 2) return 'badge bg-info';
        return 'badge bg-success';
    }

    getRiskLevelText(level) {
        const levels = {
            1: 'Very Low',
            2: 'Low',
            3: 'Medium',
            4: 'High',
            5: 'Critical'
        };
        return levels[Math.round(level)] || 'Unknown';
    }

    getModelStatusClass(model) {
        return model.trained ? 'badge bg-success' : 'badge bg-warning';
    }

    formatValue(value, type) {
        if (type === 'cost' || type === 'kpi') {
            return new Intl.NumberFormat().format(value);
        }
        if (typeof value === 'number') {
            return value.toFixed(2);
        }
        return value;
    }

    formatPercentage(value) {
        return `${((value - 1) * 100).toFixed(1)}%`;
    }
}

registry.category("actions").add("ofitec_ai_advanced.action_ai_dashboard", {
    component: AIDashboard,
    name: "AI Analytics Dashboard"
});
