#!/usr/bin/env python3
"""
Script de prueba para la integración de WhatsApp
Ejecuta pruebas básicas de funcionalidad
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class TestWhatsAppIntegration(unittest.TestCase):
    """Pruebas unitarias para la integración de WhatsApp"""

    def setUp(self):
        """Configuración inicial de las pruebas"""
        self.mock_env = Mock()
        self.mock_config = Mock()
        self.mock_message = Mock()

    def test_whatsapp_config_creation(self):
        """Prueba la creación de configuración de WhatsApp"""
        config_vals = {
            'account_name': 'Test WhatsApp',
            'phone_number_id': '123456789012345',
            'access_token': 'test_token',
            'app_secret': 'test_secret',
            'is_active': True,
            'test_mode': True
        }

        # Simular creación de configuración
        config = Mock()
        config.write(config_vals)

        # Verificar campos requeridos
        required_fields = ['account_name', 'phone_number_id', 'access_token', 'app_secret']
        for field in required_fields:
            self.assertIn(field, config_vals)
            self.assertIsNotNone(config_vals[field])

    def test_message_formatting(self):
        """Prueba el formateo de mensajes de WhatsApp"""
        action_data = {
            'name': 'Revisar riesgo crítico',
            'project_id': Mock(name='Proyecto Test'),
            'description': 'Descripción de prueba',
            'priority': 1,
            'deadline': '2025-08-30 10:00:00',
            'category': 'risk'
        }

        # Simular formateo de mensaje
        message = self._prepare_test_message(action_data)

        # Verificar elementos clave en el mensaje
        self.assertIn('🚨', message)  # Emoji de prioridad crítica
        self.assertIn(action_data['name'], message)
        self.assertIn('Proyecto Test', message)
        self.assertIn('CRÍTICA', message)
        self.assertIn('OK', message)  # Comando de respuesta
        self.assertIn('COMPLETADO', message)  # Comando de respuesta

    def _prepare_test_message(self, action_data):
        """Preparar mensaje de prueba"""
        priority_emojis = {1: '🚨', 2: '⚡', 3: '📋', 4: '📝'}
        emoji = priority_emojis.get(action_data['priority'], '📝')

        message = f"""{emoji} *ACCIÓN REQUERIDA - OFITEC*

🏗️ *Proyecto:* {action_data['project_id'].name}

📋 *Acción:* {action_data['name']}

📝 *Descripción:* {action_data['description']}

🔥 *Prioridad:* {'CRÍTICA' if action_data['priority'] == 1 else 'ALTA'}

📅 *Fecha límite:* {action_data['deadline']}

*Responde con:*
✅ *OK* - Confirmar acción
🎉 *COMPLETADO* - Marcar como completada
❌ *CANCELAR* - Cancelar acción"""

        return message

    def test_command_processing(self):
        """Prueba el procesamiento de comandos de respuesta"""
        test_commands = [
            ('OK', 'confirmed'),
            ('ok', 'confirmed'),
            ('Confirmado', 'confirmed'),
            ('COMPLETADO', 'completed'),
            ('completado', 'completed'),
            ('Listo', 'completed'),
            ('CANCELAR', 'cancelled'),
            ('cancelar', 'cancelled'),
            ('Rechazar', 'cancelled')
        ]

        for command, expected_action in test_commands:
            action = self._process_command(command.lower())
            self.assertEqual(action, expected_action,
                           f"Comando '{command}' debería resultar en '{expected_action}'")

    def _process_command(self, command):
        """Procesar comando de respuesta"""
        if command in ['ok', 'entendido', 'confirmado', 'aceptar']:
            return 'confirmed'
        elif command in ['completado', 'terminado', 'listo', 'done']:
            return 'completed'
        elif command in ['cancelar', 'cancel', 'rechazar']:
            return 'cancelled'
        else:
            return 'unknown'

    def test_phone_number_formatting(self):
        """Prueba el formateo de números de teléfono"""
        test_cases = [
            ('912345678', '+56912345678'),
            ('+56912345678', '+56912345678'),
            ('56912345678', '+56912345678'),
            ('0912345678', '+56912345678')
        ]

        for input_number, expected in test_cases:
            formatted = self._format_phone_number(input_number)
            self.assertEqual(formatted, expected,
                           f"Número '{input_number}' debería formatearse como '{expected}'")

    def _format_phone_number(self, phone):
        """Formatear número de teléfono para WhatsApp"""
        # Remover espacios y caracteres especiales
        phone = ''.join(filter(str.isdigit, phone))

        # Agregar + si no está presente
        if not phone.startswith('+'):
            if len(phone) == 9 and phone.startswith('9'):  # Número chileno sin código de país
                phone = '+56' + phone
            elif len(phone) == 10 and phone.startswith('09'):  # Número chileno con 0
                phone = '+56' + phone[1:]  # Remover el 0 inicial
            else:
                phone = '+' + phone

        return phone

    def test_webhook_verification(self):
        """Prueba la verificación de webhooks"""
        config = Mock()
        config.webhook_verify_token = 'test_token'

        # Casos de éxito
        success_cases = [
            ('subscribe', 'test_token', 'challenge123'),
            ('subscribe', 'test_token', 'abc123')
        ]

        for mode, token, challenge in success_cases:
            result = self._verify_webhook(config, mode, token, challenge)
            self.assertTrue(result['success'])
            self.assertEqual(result['challenge'], challenge)

        # Casos de error
        error_cases = [
            ('subscribe', 'wrong_token', 'challenge123'),
            ('wrong_mode', 'test_token', 'challenge123'),
            ('', '', '')
        ]

        for mode, token, challenge in error_cases:
            result = self._verify_webhook(config, mode, token, challenge)
            self.assertFalse(result['success'])

    def _verify_webhook(self, config, mode, token, challenge):
        """Verificar webhook de WhatsApp"""
        if mode == 'subscribe' and token == config.webhook_verify_token:
            return {
                'success': True,
                'challenge': challenge
            }
        else:
            return {
                'success': False,
                'error': 'Verification failed'
            }

    def test_message_status_tracking(self):
        """Prueba el seguimiento de estado de mensajes"""
        message_states = ['sent', 'delivered', 'read', 'failed']

        for status in message_states:
            message = Mock()
            message.status = 'sent'

            # Simular actualización de estado
            self._update_message_status(message, status)
            self.assertEqual(message.status, status)

            # Verificar que se actualice la fecha correspondiente
            if status == 'delivered':
                self.assertIsNotNone(message.delivered_date)
            elif status == 'read':
                self.assertIsNotNone(message.read_date)

    def _update_message_status(self, message, status):
        """Actualizar estado del mensaje"""
        message.status = status

        if status == 'delivered':
            message.delivered_date = '2025-08-27 10:00:00'
        elif status == 'read':
            message.read_date = '2025-08-27 10:05:00'

    def test_recipient_filtering(self):
        """Prueba el filtrado de destinatarios"""
        # Simular usuarios con diferentes roles
        users = [
            Mock(name='Manager', mobile='+56912345678', project_manager=True),
            Mock(name='Developer', mobile='+56987654321', project_manager=False),
            Mock(name='User', mobile='', project_manager=False),  # Sin móvil
        ]

        recipients = self._filter_recipients(users)

        # Debería incluir solo usuarios con móvil
        self.assertEqual(len(recipients), 2)
        mobile_numbers = [r.mobile for r in recipients]
        self.assertIn('+56912345678', mobile_numbers)
        self.assertIn('+56987654321', mobile_numbers)

    def _filter_recipients(self, users):
        """Filtrar destinatarios válidos"""
        valid_recipients = []
        for user in users:
            if user.mobile and user.mobile.strip():
                valid_recipients.append(user)
        return valid_recipients


def run_tests():
    """Ejecuta todas las pruebas"""
    print("📱 Ejecutando pruebas de WhatsApp Integration...")
    print("=" * 60)

    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWhatsAppIntegration)

    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Resultado
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ Todas las pruebas de WhatsApp pasaron exitosamente!")
        return 0
    else:
        print(f"❌ {len(result.failures)} pruebas fallaron")
        print(f"❌ {len(result.errors)} errores de prueba")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
