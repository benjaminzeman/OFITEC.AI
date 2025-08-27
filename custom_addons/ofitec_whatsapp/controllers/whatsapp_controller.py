# -*- coding: utf-8 -*-
"""
WhatsApp Webhook Controller
Handles incoming WhatsApp webhooks for OFITEC.AI
"""

import json
import hmac
import hashlib
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WhatsAppWebhookController(http.Controller):
    """Controller for WhatsApp Business API webhooks"""

    @http.route('/webhooks/whatsapp/<int:config_id>', type='http', auth='public',
                methods=['GET', 'POST'], csrf=False)
    def whatsapp_webhook(self, config_id, **kwargs):
        """Handle WhatsApp webhook requests"""

        if request.httprequest.method == 'GET':
            return self._handle_webhook_verification(config_id, kwargs)
        elif request.httprequest.method == 'POST':
            return self._handle_webhook_message(config_id)
        else:
            return self._error_response("Method not allowed", 405)

    def _handle_webhook_verification(self, config_id, kwargs):
        """Handle webhook verification from WhatsApp"""
        try:
            # Get configuration
            config = request.env['ofitec.whatsapp.config'].sudo().browse(config_id)
            if not config.exists():
                _logger.error(f"WhatsApp config {config_id} not found")
                return self._error_response("Configuration not found", 404)

            # Verify token
            mode = kwargs.get('hub.mode')
            token = kwargs.get('hub.verify_token')
            challenge = kwargs.get('hub.challenge')

            if mode == 'subscribe' and token == config.webhook_verify_token:
                _logger.info(f"WhatsApp webhook verified for config {config_id}")
                return challenge
            else:
                _logger.warning(f"WhatsApp webhook verification failed for config {config_id}")
                return self._error_response("Verification failed", 403)

        except Exception as e:
            _logger.error(f"Error during webhook verification: {e}")
            return self._error_response("Internal server error", 500)

    def _handle_webhook_message(self, config_id):
        """Handle incoming webhook message from WhatsApp"""
        try:
            # Get configuration
            config = request.env['ofitec.whatsapp.config'].sudo().browse(config_id)
            if not config.exists():
                _logger.error(f"WhatsApp config {config_id} not found")
                return self._error_response("Configuration not found", 404)

            # Verify request signature if app secret is configured
            if config.app_secret:
                if not self._verify_signature(config.app_secret):
                    _logger.warning("Invalid webhook signature")
                    return self._error_response("Invalid signature", 401)

            # Parse webhook data
            webhook_data = json.loads(request.httprequest.data.decode('utf-8'))

            _logger.info(f"Received WhatsApp webhook: {json.dumps(webhook_data, indent=2)}")

            # Process webhook
            webhook_handler = request.env['ofitec.whatsapp.webhook'].sudo()
            success = webhook_handler.process_webhook(config_id, webhook_data)

            if success:
                return "OK"
            else:
                return self._error_response("Processing failed", 500)

        except json.JSONDecodeError as e:
            _logger.error(f"Invalid JSON in webhook: {e}")
            return self._error_response("Invalid JSON", 400)
        except Exception as e:
            _logger.error(f"Error processing webhook: {e}")
            return self._error_response("Internal server error", 500)

    def _verify_signature(self, app_secret):
        """Verify webhook signature from WhatsApp"""
        try:
            signature = request.httprequest.headers.get('X-Hub-Signature-256', '')
            if not signature:
                return False

            # Remove 'sha256=' prefix
            signature = signature.replace('sha256=', '')

            # Create expected signature
            expected_signature = hmac.new(
                app_secret.encode('utf-8'),
                request.httprequest.data,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            _logger.error(f"Error verifying signature: {e}")
            return False

    def _error_response(self, message, status_code):
        """Return error response"""
        _logger.error(f"Webhook error {status_code}: {message}")
        return request.make_response(
            json.dumps({'error': message}),
            headers=[('Content-Type', 'application/json')],
            status=status_code
        )


class WhatsAppAPIController(http.Controller):
    """Controller for WhatsApp API operations"""

    @http.route('/api/whatsapp/send_message', type='json', auth='user', methods=['POST'])
    def send_message(self, **kwargs):
        """Send WhatsApp message via API"""
        try:
            # Get parameters
            config_id = kwargs.get('config_id')
            to_phone = kwargs.get('to_phone')
            message = kwargs.get('message')
            message_type = kwargs.get('message_type', 'text')

            if not all([config_id, to_phone, message]):
                return {
                    'success': False,
                    'error': 'Missing required parameters: config_id, to_phone, message'
                }

            # Get configuration
            config = request.env['ofitec.whatsapp.config'].browse(config_id)
            if not config.exists():
                return {
                    'success': False,
                    'error': 'WhatsApp configuration not found'
                }

            # Send message
            result = config.send_message(to_phone, message, message_type)

            return result

        except Exception as e:
            _logger.error(f"Error sending WhatsApp message via API: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/whatsapp/test_connection', type='json', auth='user', methods=['POST'])
    def test_connection(self, **kwargs):
        """Test WhatsApp connection via API"""
        try:
            config_id = kwargs.get('config_id')
            if not config_id:
                return {
                    'success': False,
                    'error': 'Missing config_id parameter'
                }

            # Get configuration
            config = request.env['ofitec.whatsapp.config'].browse(config_id)
            if not config.exists():
                return {
                    'success': False,
                    'error': 'WhatsApp configuration not found'
                }

            # Test connection
            result = config.test_connection()

            return result

        except Exception as e:
            _logger.error(f"Error testing WhatsApp connection: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/whatsapp/get_stats', type='json', auth='user', methods=['GET'])
    def get_stats(self, **kwargs):
        """Get WhatsApp statistics via API"""
        try:
            config_id = kwargs.get('config_id')
            if not config_id:
                return {
                    'success': False,
                    'error': 'Missing config_id parameter'
                }

            # Get configuration
            config = request.env['ofitec.whatsapp.config'].browse(config_id)
            if not config.exists():
                return {
                    'success': False,
                    'error': 'WhatsApp configuration not found'
                }

            # Get statistics
            stats = {
                'messages_sent_today': config.messages_sent_today,
                'messages_received_today': config.messages_received_today,
                'is_active': config.is_active,
                'test_mode': config.test_mode
            }

            return {
                'success': True,
                'stats': stats
            }

        except Exception as e:
            _logger.error(f"Error getting WhatsApp stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }
