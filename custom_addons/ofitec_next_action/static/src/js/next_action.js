/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onMounted, useState } from "owl";
import { useService } from "@web/core/utils/hooks";

export class NextActionDashboard extends Component {
    setup() {
        this.state = useState({
            dashboardData: {
                summary: {
                    pending: 0,
                    in_progress: 0,
                    completed_today: 0,
                    critical: 0,
                    high: 0
                },
                urgent_actions: []
            },
            whatsappStats: {
                messages_sent: 0,
                messages_received: 0,
                is_connected: false
            },
            isLoading: false
        });

        this.rpc = useService("rpc");
        this.notification = useService("notification");

        onMounted(() => {
            this.loadDashboardData();
            this.loadWhatsAppStats();
        });
    }

    async loadDashboardData() {
        this.state.isLoading = true;

        try {
            const data = await this.rpc("/web/dataset/call_kw", {
                model: "ofitec.next.action",
                method: "get_dashboard_data",
                args: [],
                kwargs: {}
            });

            this.state.dashboardData = data;
            this.updateMetricsDisplay();

        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.notification.add("Error al cargar datos del dashboard", {
                type: "danger"
            });
        }

        this.state.isLoading = false;
    }

    async loadWhatsAppStats() {
        try {
            const stats = await this.rpc("/api/whatsapp/get_stats", {
                config_id: 1  // Default config ID, should be configurable
            });

            if (stats.success) {
                this.state.whatsappStats = stats.stats;
            }
        } catch (error) {
            console.warn("WhatsApp stats not available:", error);
            // WhatsApp not configured, that's OK
        }
    }

    updateMetricsDisplay() {
        // Actualizar contadores en el DOM
        const metrics = this.state.dashboardData.summary;

        this.updateMetric('critical-count', metrics.critical);
        this.updateMetric('high-count', metrics.high);
        this.updateMetric('pending-count', metrics.pending);
        this.updateMetric('completed-count', metrics.completed_today);

        // Actualizar lista de acciones urgentes
        this.updateUrgentActionsList();
    }

    updateMetric(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    updateUrgentActionsList() {
        const container = document.getElementById('urgent-actions-list');
        if (!container) return;

        const actions = this.state.dashboardData.urgent_actions;

        if (actions.length === 0) {
            container.innerHTML = '<div class="no-actions">🎉 No hay acciones urgentes pendientes</div>';
            return;
        }

        const actionsHtml = actions.map(action => `
            <div class="urgent-action-item priority-${action.priority}">
                <div class="action-header">
                    <span class="action-priority">P${action.priority}</span>
                    <span class="action-category">${this.getCategoryIcon(action.category)}</span>
                    <span class="action-project">${action.project}</span>
                    ${action.whatsapp_sent ? '<span class="whatsapp-sent">📱</span>' : ''}
                </div>
                <div class="action-title">${action.name}</div>
                <div class="action-deadline">
                    📅 ${action.deadline || 'Sin fecha límite'}
                </div>
                <div class="action-actions">
                    <button class="btn btn-sm btn-primary" onclick="window.open('/web#id=${action.id}&model=ofitec.next.action&view_type=form', '_blank')">
                        Ver Detalles
                    </button>
                    ${!action.whatsapp_sent ? `
                    <button class="btn btn-sm btn-success" onclick="dashboardComponent.sendWhatsAppReminder(${action.id})">
                        📱 WhatsApp
                    </button>
                    ` : ''}
                </div>
            </div>
        `).join('');

        container.innerHTML = actionsHtml;
    }

    getCategoryIcon(category) {
        const icons = {
            'risk': '🎯',
            'financial': '💰',
            'operational': '⚙️',
            'quality': '🛡️',
            'communication': '📱',
            'planning': '📋'
        };
        return icons[category] || '📝';
    }

    async runAIAnalysis() {
        this.state.isLoading = true;

        try {
            const result = await this.rpc("/web/dataset/call_kw", {
                model: "ofitec.next.action",
                method: "run_ai_analysis",
                args: [],
                kwargs: {}
            });

            this.notification.add(result.message, {
                type: "success"
            });

            // Recargar datos
            await this.loadDashboardData();

        } catch (error) {
            console.error("Error running AI analysis:", error);
            this.notification.add("Error al ejecutar análisis de IA", {
                type: "danger"
            });
        }

        this.state.isLoading = false;
    }

    async generateRecommendations() {
        this.state.isLoading = true;

        try {
            const count = await this.rpc("/web/dataset/call_kw", {
                model: "ofitec.next.action",
                method: "generate_next_actions",
                args: [],
                kwargs: {}
            });

            this.notification.add(`Se generaron ${count} recomendaciones inteligentes`, {
                type: "success"
            });

            // Recargar datos
            await this.loadDashboardData();

        } catch (error) {
            console.error("Error generating recommendations:", error);
            this.notification.add("Error al generar recomendaciones", {
                type: "danger"
            });
        }

        this.state.isLoading = false;
    }

    async sendWhatsAppReminder(actionId) {
        try {
            const result = await this.rpc("/web/dataset/call_kw", {
                model: "ofitec.next.action",
                method: "send_whatsapp_reminder",
                args: [actionId],
                kwargs: {}
            });

            if (result.success) {
                this.notification.add("Recordatorio enviado por WhatsApp", {
                    type: "success"
                });
                // Recargar datos para actualizar el estado
                await this.loadDashboardData();
            } else {
                this.notification.add(`Error al enviar WhatsApp: ${result.error}`, {
                    type: "danger"
                });
            }
        } catch (error) {
            console.error("Error sending WhatsApp reminder:", error);
            this.notification.add("Error al enviar recordatorio por WhatsApp", {
                type: "danger"
            });
        }
    }

    getPriorityColor(priority) {
        const colors = {
            '1': '#dc3545', // red
            '2': '#fd7e14', // orange
            '3': '#ffc107', // yellow
            '4': '#28a745'  // green
        };
        return colors[priority] || '#6c757d';
    }

    getPriorityLabel(priority) {
        const labels = {
            '1': 'Crítica',
            '2': 'Alta',
            '3': 'Media',
            '4': 'Baja'
        };
        return labels[priority] || 'Sin definir';
    }
}

NextActionDashboard.template = "ofitec_next_action.NextActionDashboard";

// Registrar el componente
registry.category("actions").add("ofitec_next_action.dashboard", NextActionDashboard);
