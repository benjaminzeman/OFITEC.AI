/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onMounted, useState } from "owl";
import { useService } from "@web/core/utils/hooks";

export class CommandPalette extends Component {
    setup() {
        this.state = useState({
            query: "",
            results: [],
            showPalette: false,
            isLoading: false,
            commandHistory: [],
            suggestions: []
        });

        this.rpc = useService("rpc");
        this.notification = useService("notification");

        onMounted(() => {
            document.addEventListener("keydown", this.onKeyDown.bind(this));
            this.loadCommandHistory();
            this.loadSuggestions();
        });
    }

    onKeyDown(event) {
        if (event.ctrlKey && event.key === "k") {
            event.preventDefault();
            this.togglePalette();
        } else if (event.key === "Escape" && this.state.showPalette) {
            this.state.showPalette = false;
        } else if (event.key === "Enter" && this.state.showPalette) {
            event.preventDefault();
            this.executeCommand(this.state.query);
        }
    }

    togglePalette() {
        this.state.showPalette = !this.state.showPalette;
        if (this.state.showPalette) {
            // Focus on input when opening
            setTimeout(() => {
                const input = document.querySelector('.command-input');
                if (input) input.focus();
            }, 100);
        }
    }

    async onInput(event) {
        this.state.query = event.target.value;

        if (this.state.query.length > 1) {
            this.state.isLoading = true;

            try {
                // Get suggestions from backend
                const suggestions = await this.rpc("/web/dataset/call_kw", {
                    model: "ofitec.command.palette",
                    method: "get_command_suggestions",
                    args: [this.state.query],
                    kwargs: {}
                });

                this.state.suggestions = suggestions;
            } catch (error) {
                console.error("Error loading suggestions:", error);
                this.state.suggestions = [];
            }

            this.state.isLoading = false;
        } else {
            this.state.suggestions = [];
        }
    }

    async executeCommand(commandText = null) {
        const command = commandText || this.state.query;

        if (!command.trim()) {
            this.notification.add("Por favor ingresa un comando", {
                type: "warning"
            });
            return;
        }

        this.state.isLoading = true;

        try {
            // Execute command via RPC
            const result = await this.rpc("/web/dataset/call_kw", {
                model: "ofitec.command.palette",
                method: "execute_command",
                args: [command],
                kwargs: { context: this.getCurrentContext() }
            });

            // Display result
            this.displayResult(result);

            // Add to history
            this.addToHistory(command, result);

            // Close palette if it's a simple action
            if (result.type === 'action' || result.type === 'daily_report_created') {
                setTimeout(() => {
                    this.state.showPalette = false;
                }, 2000);
            }

        } catch (error) {
            console.error("Error executing command:", error);
            this.notification.add("Error al ejecutar el comando", {
                type: "danger"
            });
        }

        this.state.isLoading = false;
    }

    displayResult(result) {
        const resultContainer = document.getElementById('commandResult');
        if (!resultContainer) return;

        let html = '';

        switch (result.type) {
            case 'project_status':
                html = this.renderProjectStatus(result);
                break;
            case 'risk_analysis':
                html = this.renderRiskAnalysis(result);
                break;
            case 'cost_analysis':
                html = this.renderCostAnalysis(result);
                break;
            case 'daily_report_created':
                html = this.renderReportCreated(result);
                break;
            case 'help':
                html = this.renderHelp(result);
                break;
            case 'error':
                html = this.renderError(result);
                break;
            default:
                html = this.renderGeneric(result);
        }

        resultContainer.innerHTML = html;
    }

    renderProjectStatus(result) {
        if (result.project) {
            return `
                <div class="alert alert-info">
                    <h5>📊 Estado del Proyecto: ${result.project}</h5>
                    <p><strong>Progreso:</strong> ${result.progress}%</p>
                    <p><strong>Reportes Recientes:</strong> ${result.recent_reports}</p>
                    ${result.last_report ? `<p><strong>Último Reporte:</strong> ${result.last_report}</p>` : ''}
                </div>
            `;
        } else {
            return `
                <div class="alert alert-info">
                    <h5>📊 Resumen General</h5>
                    <p><strong>Total de Proyectos:</strong> ${result.total_projects}</p>
                    <p><strong>Proyectos Activos:</strong> ${result.active_projects}</p>
                    <p><strong>Progreso Promedio:</strong> ${result.avg_progress}%</p>
                </div>
            `;
        }
    }

    renderRiskAnalysis(result) {
        let categoriesHtml = '';
        for (const [category, count] of Object.entries(result.categories || {})) {
            categoriesHtml += `<li>${category}: ${count}</li>`;
        }

        return `
            <div class="alert alert-warning">
                <h5>🎯 Análisis de Riesgos</h5>
                <p><strong>Total de Riesgos:</strong> ${result.total_risks}</p>
                <p><strong>Riesgos Críticos:</strong> ${result.critical_risks}</p>
                <p><strong>Riesgos Altos:</strong> ${result.high_risks}</p>
                ${categoriesHtml ? `<p><strong>Por Categoría:</strong></p><ul>${categoriesHtml}</ul>` : ''}
            </div>
        `;
    }

    renderCostAnalysis(result) {
        if (result.message) {
            return `<div class="alert alert-info"><h5>💰 Análisis de Costos</h5><p>${result.message}</p></div>`;
        }

        return `
            <div class="alert alert-success">
                <h5>💰 Análisis de Costos</h5>
                <p><strong>Presupuesto Total:</strong> $${result.total_budget?.toLocaleString() || 'N/A'}</p>
                <p><strong>Costo Real:</strong> $${result.total_cost?.toLocaleString() || 'N/A'}</p>
                <p><strong>Varianza Promedio:</strong> ${result.avg_variance?.toFixed(2) || 'N/A'}%</p>
                <p><strong>Proyectos Analizados:</strong> ${result.projects_count || 'N/A'}</p>
            </div>
        `;
    }

    renderReportCreated(result) {
        return `
            <div class="alert alert-success">
                <h5>✅ Reporte Creado Exitosamente</h5>
                <p>${result.message}</p>
                <p><strong>ID del Reporte:</strong> ${result.report_id}</p>
            </div>
        `;
    }

    renderHelp(result) {
        return `
            <div class="alert alert-info">
                <h5>💡 Ayuda - Comandos Disponibles</h5>
                <p>${result.message}</p>
                <div class="command-examples">
                    <p><strong>Ejemplos:</strong></p>
                    <ul>
                        <li>"estado del proyecto" - Ver estado actual</li>
                        <li>"analizar riesgos" - Análisis de riesgos</li>
                        <li>"resumen costos" - Resumen financiero</li>
                        <li>"crear reporte diario" - Nuevo reporte</li>
                        <li>"predecir costos" - Predicción con IA</li>
                    </ul>
                </div>
            </div>
        `;
    }

    renderError(result) {
        return `
            <div class="alert alert-danger">
                <h5>❌ Error</h5>
                <p>${result.message}</p>
            </div>
        `;
    }

    renderGeneric(result) {
        return `
            <div class="alert alert-secondary">
                <h5>📄 Resultado</h5>
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </div>
        `;
    }

    getCurrentContext() {
        // Get current context (project, user, etc.)
        return {
            user_id: this.env.user.id,
            // Add more context as needed
        };
    }

    addToHistory(command, result) {
        const historyItem = {
            command: command,
            result: result,
            timestamp: new Date().toISOString()
        };

        this.state.commandHistory.unshift(historyItem);

        // Keep only last 10 items
        if (this.state.commandHistory.length > 10) {
            this.state.commandHistory = this.state.commandHistory.slice(0, 10);
        }

        // Save to localStorage
        localStorage.setItem('commandPaletteHistory', JSON.stringify(this.state.commandHistory));
    }

    loadCommandHistory() {
        const history = localStorage.getItem('commandPaletteHistory');
        if (history) {
            try {
                this.state.commandHistory = JSON.parse(history);
            } catch (error) {
                console.error("Error loading command history:", error);
                this.state.commandHistory = [];
            }
        }
    }

    loadSuggestions() {
        // Load predefined suggestions
        this.state.suggestions = [
            { name: "Estado del Proyecto", description: "Ver estado actual del proyecto" },
            { name: "Analizar Riesgos", description: "Análisis completo de riesgos" },
            { name: "Resumen Costos", description: "Resumen financiero del proyecto" },
            { name: "Crear Reporte Diario", description: "Generar nuevo reporte de obra" },
            { name: "Predecir Costos", description: "Predicción de costos con IA" }
        ];
    }

    selectSuggestion(suggestion) {
        this.state.query = suggestion.name.toLowerCase();
        this.executeCommand(suggestion.name.toLowerCase());
    }
}

CommandPalette.template = "of_command_palette.CommandPalette";

registry.category("components").add("CommandPalette", CommandPalette);
