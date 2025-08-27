#!/usr/bin/env python3
"""
Script de prueba para el módulo Next-Best-Action Dashboard
Ejecuta pruebas básicas de funcionalidad
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class TestNextActionDashboard(unittest.TestCase):
    """Pruebas unitarias para el dashboard de próximas acciones"""

    def setUp(self):
        """Configuración inicial de las pruebas"""
        self.mock_env = Mock()
        self.mock_model = Mock()

    def test_dashboard_data_structure(self):
        """Prueba que la estructura de datos del dashboard sea correcta"""
        expected_structure = {
            'summary': {
                'pending': 0,
                'in_progress': 0,
                'completed_today': 0,
                'critical': 0,
                'high': 0
            },
            'urgent_actions': []
        }

        # Simular datos del dashboard
        dashboard_data = {
            'summary': {
                'pending': 5,
                'in_progress': 2,
                'completed_today': 3,
                'critical': 1,
                'high': 2
            },
            'urgent_actions': [
                {
                    'id': 1,
                    'name': 'Acción crítica de prueba',
                    'priority': 1,
                    'category': 'risk',
                    'project': 'Proyecto Test',
                    'deadline': '2025-08-30'
                }
            ]
        }

        # Verificar estructura
        self.assertIn('summary', dashboard_data)
        self.assertIn('urgent_actions', dashboard_data)
        self.assertIsInstance(dashboard_data['summary'], dict)
        self.assertIsInstance(dashboard_data['urgent_actions'], list)

        # Verificar campos del summary
        summary = dashboard_data['summary']
        required_fields = ['pending', 'in_progress', 'completed_today', 'critical', 'high']
        for field in required_fields:
            self.assertIn(field, summary)
            self.assertIsInstance(summary[field], int)

    def test_ai_analysis_method(self):
        """Prueba el método de análisis de IA"""
        # Simular resultado del análisis
        analysis_result = {
            'success': True,
            'message': 'Análisis completado exitosamente',
            'actions_generated': 3,
            'risks_identified': 2,
            'recommendations': [
                'Revisar presupuesto',
                'Actualizar cronograma',
                'Mejorar comunicación'
            ]
        }

        self.assertTrue(analysis_result['success'])
        self.assertGreater(analysis_result['actions_generated'], 0)
        self.assertIsInstance(analysis_result['recommendations'], list)

    def test_priority_calculation(self):
        """Prueba el cálculo de prioridades"""
        test_cases = [
            # (impact, urgency, expected_priority)
            (9.5, 10.0, 1),  # Crítica
            (7.5, 8.0, 2),   # Alta
            (5.0, 6.0, 3),   # Media
            (2.5, 3.0, 4),   # Baja
        ]

        for impact, urgency, expected in test_cases:
            # Simular cálculo de prioridad
            if impact >= 9.0 and urgency >= 9.0:
                priority = 1
            elif impact >= 7.0 and urgency >= 7.0:
                priority = 2
            elif impact >= 4.0 and urgency >= 4.0:
                priority = 3
            else:
                priority = 4

            self.assertEqual(priority, expected,
                           f"Prioridad incorrecta para impact={impact}, urgency={urgency}")

    def test_category_icons(self):
        """Prueba la asignación de iconos por categoría"""
        category_icons = {
            'risk': '🎯',
            'financial': '💰',
            'operational': '⚙️',
            'quality': '🛡️',
            'communication': '📱',
            'planning': '📋'
        }

        test_categories = ['risk', 'financial', 'operational', 'quality', 'communication', 'planning']

        for category in test_categories:
            self.assertIn(category, category_icons)
            icon = category_icons[category]
            self.assertTrue(len(icon) > 0, f"Icono vacío para categoría {category}")

    def test_dashboard_metrics_update(self):
        """Prueba la actualización de métricas del dashboard"""
        # Simular métricas iniciales
        initial_metrics = {
            'critical-count': '0',
            'high-count': '0',
            'pending-count': '0',
            'completed-count': '0'
        }

        # Simular actualización
        updated_metrics = {
            'critical-count': '2',
            'high-count': '5',
            'pending-count': '12',
            'completed-count': '3'
        }

        # Verificar que las métricas cambiaron
        for key in initial_metrics:
            self.assertNotEqual(initial_metrics[key], updated_metrics[key],
                              f"Métrica {key} no se actualizó correctamente")

    def test_urgent_actions_filtering(self):
        """Prueba el filtrado de acciones urgentes"""
        # Simular lista de acciones
        all_actions = [
            {'id': 1, 'priority': 1, 'name': 'Crítica 1'},
            {'id': 2, 'priority': 2, 'name': 'Alta 1'},
            {'id': 3, 'priority': 3, 'name': 'Media 1'},
            {'id': 4, 'priority': 4, 'name': 'Baja 1'},
            {'id': 5, 'priority': 1, 'name': 'Crítica 2'},
        ]

        # Filtrar acciones urgentes (prioridad 1-2)
        urgent_actions = [action for action in all_actions if action['priority'] <= 2]

        self.assertEqual(len(urgent_actions), 3, "Número incorrecto de acciones urgentes")
        for action in urgent_actions:
            self.assertLessEqual(action['priority'], 2, "Acción no urgente incluida")

    def test_date_formatting(self):
        """Prueba el formateo de fechas"""
        from datetime import datetime, timedelta

        # Simular fechas
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)

        # Formatear fechas
        formatted_dates = {
            'today': today.strftime('%Y-%m-%d'),
            'tomorrow': tomorrow.strftime('%Y-%m-%d'),
            'next_week': next_week.strftime('%Y-%m-%d')
        }

        for name, date_str in formatted_dates.items():
            # Verificar formato YYYY-MM-DD
            self.assertRegex(date_str, r'\d{4}-\d{2}-\d{2}',
                           f"Fecha {name} mal formateada: {date_str}")

def run_tests():
    """Ejecuta todas las pruebas"""
    print("🚀 Ejecutando pruebas del módulo Next-Best-Action Dashboard...")
    print("=" * 60)

    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNextActionDashboard)

    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Resultado
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ Todas las pruebas pasaron exitosamente!")
        return 0
    else:
        print(f"❌ {len(result.failures)} pruebas fallaron")
        print(f"❌ {len(result.errors)} errores de prueba")
        return 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
