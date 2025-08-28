# -*- coding: utf-8 -*-
"""
WhatsApp Business Integration Module
Handles WhatsApp Business API integration for OFITEC.AI
"""

import logging
import json
import requests
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WhatsAppConfig(models.Model):
    """Configuration for WhatsApp Business API"""

    _name = "ofitec.whatsapp.config"
    _description = "WhatsApp Business API Configuration"
    _rec_name = "account_name"

    # Basic Configuration
    account_name = fields.Char(string="Account Name", required=True)
    phone_number_id = fields.Char(
        string="Phone Number ID",
        required=True,
        help="WhatsApp Business Phone Number ID",
    )
    access_token = fields.Char(
        string="Access Token", required=True, help="WhatsApp Business API Access Token"
    )
    app_secret = fields.Char(
        string="App Secret", required=True, help="WhatsApp Business App Secret"
    )

    # API Configuration
    api_version = fields.Selection(
        [
            ("v18.0", "v18.0"),
            ("v17.0", "v17.0"),
            ("v16.0", "v16.0"),
        ],
        string="API Version",
        default="v18.0",
        required=True,
    )

    base_url = fields.Char(string="Base URL", compute="_compute_base_url", store=True)

    # Status and Settings
    is_active = fields.Boolean(string="Active", default=True)
    test_mode = fields.Boolean(
        string="Test Mode",
        default=False,
        help="Send test messages to verify configuration",
    )

    # Webhook Configuration
    webhook_verify_token = fields.Char(
        string="Webhook Verify Token", help="Token for webhook verification"
    )
    webhook_url = fields.Char(string="Webhook URL", compute="_compute_webhook_url")

    # Message Templates
    default_language = fields.Selection(
        [
            ("es", "Spanish"),
            ("en", "English"),
            ("pt", "Portuguese"),
        ],
        string="Default Language",
        default="es",
        required=True,
    )

    # Statistics
    messages_sent_today = fields.Integer(
        string="Messages Sent Today", compute="_compute_stats", store=False
    )
    messages_received_today = fields.Integer(
        string="Messages Received Today", compute="_compute_stats", store=False
    )

    @api.depends("api_version")
    def _compute_base_url(self):
        """Compute the base URL for WhatsApp API"""
        for record in self:
            record.base_url = f"https://graph.facebook.com/{record.api_version}"

    @api.depends("webhook_verify_token")
    def _compute_webhook_url(self):
        """Compute webhook URL for this configuration"""
        for record in self:
            if record.webhook_verify_token:
                base_url = (
                    self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                )
                record.webhook_url = f"{base_url}/webhooks/whatsapp/{record.id}"
            else:
                record.webhook_url = False

    @api.depends()
    def _compute_stats(self):
        """Compute message statistics for today"""
        today = datetime.now().date()
        for record in self:
            # Messages sent
            sent_count = self.env["ofitec.whatsapp.message"].search_count(
                [
                    ("config_id", "=", record.id),
                    ("direction", "=", "outbound"),
                    ("create_date", ">=", today.strftime("%Y-%m-%d 00:00:00")),
                    ("create_date", "<=", today.strftime("%Y-%m-%d 23:59:59")),
                ]
            )
            record.messages_sent_today = sent_count

            # Messages received
            received_count = self.env["ofitec.whatsapp.message"].search_count(
                [
                    ("config_id", "=", record.id),
                    ("direction", "=", "inbound"),
                    ("create_date", ">=", today.strftime("%Y-%m-%d 00:00:00")),
                    ("create_date", "<=", today.strftime("%Y-%m-%d 23:59:59")),
                ]
            )
            record.messages_received_today = received_count

    @api.model
    def get_active_config(self):
        """Get the active WhatsApp configuration"""
        config = self.search([("is_active", "=", True)], limit=1)
        if not config:
            raise UserError(
                _(
                    "No active WhatsApp configuration found. Please configure WhatsApp first."
                )
            )
        return config

    def _get_param(self, key, default=None):
        # Helper to fetch secure params from ir.config_parameter
        icp = self.env["ir.config_parameter"].sudo()
        return icp.get_param(key, default)

    def test_connection(self):
        """Test WhatsApp API connection"""
        self.ensure_one()

        try:
            # Preferir parámetros del sistema si están definidos
            phone_id = self._get_param(
                "ofitec_whatsapp.phone_number_id", self.phone_number_id
            )
            access_token = self._get_param(
                "ofitec_whatsapp.access_token", self.access_token
            )
            url = f"{self.base_url}/{phone_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "message": _("Connection successful! Phone number: %(phone)s")
                % {"phone": data.get("display_phone_number", "Unknown")},
            }

        except requests.exceptions.RequestException as e:
            _logger.error(f"WhatsApp API connection test failed: {e}")
            return {
                "success": False,
                "message": _("Connection failed: %(error)s") % {"error": str(e)},
            }

    def send_message(self, to_phone, message_text, message_type="text"):
        """Send a message via WhatsApp API"""
        self.ensure_one()

        if not self.is_active:
            raise UserError(_("WhatsApp configuration is not active"))

        try:
            phone_id = self._get_param(
                "ofitec_whatsapp.phone_number_id", self.phone_number_id
            )
            access_token = self._get_param(
                "ofitec_whatsapp.access_token", self.access_token
            )
            url = f"{self.base_url}/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_phone,
                "type": message_type,
            }

            if message_type == "text":
                payload["text"] = {"body": message_text}
            elif message_type == "template":
                # Handle template messages
                payload.update(message_text)

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Create message record
            message_vals = {
                "config_id": self.id,
                "direction": "outbound",
                "to_phone": to_phone,
                "message_type": message_type,
                "content": json.dumps(payload),
                "status": "sent",
                "whatsapp_message_id": data.get("messages", [{}])[0].get("id"),
                "response_data": json.dumps(data),
            }

            self.env["ofitec.whatsapp.message"].create(message_vals)

            return {
                "success": True,
                "message_id": data.get("messages", [{}])[0].get("id"),
                "data": data,
            }

        except requests.exceptions.RequestException as e:
            _logger.error(f"Failed to send WhatsApp message: {e}")

            # Create failed message record
            message_vals = {
                "config_id": self.id,
                "direction": "outbound",
                "to_phone": to_phone,
                "message_type": message_type,
                "content": message_text,
                "status": "failed",
                "error_message": str(e),
            }
            self.env["ofitec.whatsapp.message"].create(message_vals)

            return {"success": False, "error": str(e)}

    def send_template_message(
        self, to_phone, template_name, language_code=None, components=None
    ):
        """Send a template message"""
        if not language_code:
            language_code = self.default_language

        template_data = {"name": template_name, "language": {"code": language_code}}

        if components:
            template_data["components"] = components

        return self.send_message(to_phone, template_data, "template")


class WhatsAppMessage(models.Model):
    """WhatsApp message log and management"""

    _name = "ofitec.whatsapp.message"
    _description = "WhatsApp Message Log"
    _order = "create_date desc"

    # Basic Information
    config_id = fields.Many2one(
        "ofitec.whatsapp.config",
        string="WhatsApp Config",
        required=True,
        ondelete="cascade",
    )
    direction = fields.Selection(
        [("inbound", "Inbound"), ("outbound", "Outbound")],
        string="Direction",
        required=True,
    )

    # Contact Information
    from_phone = fields.Char(string="From Phone")
    to_phone = fields.Char(string="To Phone")

    # Message Content
    message_type = fields.Selection(
        [
            ("text", "Text"),
            ("image", "Image"),
            ("document", "Document"),
            ("audio", "Audio"),
            ("video", "Video"),
            ("location", "Location"),
            ("contacts", "Contacts"),
            ("sticker", "Sticker"),
            ("template", "Template"),
        ],
        string="Message Type",
        default="text",
    )

    content = fields.Text(string="Message Content")
    media_url = fields.Char(string="Media URL")
    media_caption = fields.Text(string="Media Caption")

    # Status and Tracking
    status = fields.Selection(
        [
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("read", "Read"),
            ("failed", "Failed"),
            ("pending", "Pending"),
        ],
        string="Status",
        default="pending",
    )

    whatsapp_message_id = fields.Char(string="WhatsApp Message ID")
    response_data = fields.Text(string="API Response")

    # Error Handling
    error_message = fields.Text(string="Error Message")
    retry_count = fields.Integer(string="Retry Count", default=0)

    # Related Records
    next_action_id = fields.Many2one(
        "ofitec.next.action", string="Related Action", ondelete="set null"
    )
    user_id = fields.Many2one("res.users", string="Related User", ondelete="set null")

    # Metadata
    create_date = fields.Datetime(string="Created", readonly=True)
    sent_date = fields.Datetime(string="Sent Date")
    delivered_date = fields.Datetime(string="Delivered Date")
    read_date = fields.Datetime(string="Read Date")

    @api.model
    def create_from_webhook(self, webhook_data, config):
        """Create message from webhook data"""
        message_data = (
            webhook_data.get("messages", [{}])[0]
            if webhook_data.get("messages")
            else {}
        )

        if not message_data:
            return False

        vals = {
            "config_id": config.id,
            "direction": "inbound",
            "from_phone": message_data.get("from"),
            "whatsapp_message_id": message_data.get("id"),
            "message_type": message_data.get("type", "text"),
            "status": "delivered",
            "delivered_date": datetime.now(),
        }

        # Handle different message types
        if message_data.get("type") == "text":
            vals["content"] = message_data.get("text", {}).get("body", "")
        elif message_data.get("type") in ["image", "document", "audio", "video"]:
            media_data = message_data.get(message_data["type"], {})
            vals["media_url"] = media_data.get("url")
            vals["media_caption"] = media_data.get("caption", "")

        return self.create(vals)

    def mark_as_read(self):
        """Mark message as read"""
        self.write({"status": "read", "read_date": datetime.now()})

    def retry_send(self):
        """Retry sending failed message"""
        for message in self.filtered(
            lambda m: m.direction == "outbound" and m.status == "failed"
        ):
            if message.retry_count < 3:
                config = message.config_id
                result = config.send_message(
                    message.to_phone, message.content, message.message_type
                )

                if result["success"]:
                    message.write(
                        {
                            "status": "sent",
                            "retry_count": message.retry_count + 1,
                            "error_message": False,
                        }
                    )
                else:
                    message.write(
                        {
                            "retry_count": message.retry_count + 1,
                            "error_message": result["error"],
                        }
                    )


class WhatsAppWebhook(models.Model):
    """Handle WhatsApp webhooks"""

    _name = "ofitec.whatsapp.webhook"
    _description = "WhatsApp Webhook Handler"

    @api.model
    def process_webhook(self, config_id, webhook_data):
        """Process incoming webhook from WhatsApp"""
        config = self.env["ofitec.whatsapp.config"].browse(config_id)
        if not config.exists():
            _logger.error(f"WhatsApp config {config_id} not found")
            return False

        try:
            # Verify webhook data
            if not self._verify_webhook_data(webhook_data):
                _logger.warning("Invalid webhook data received")
                return False

            # Process different webhook types
            webhook_type = webhook_data.get("field")

            if webhook_type == "messages":
                return self._process_message_webhook(config, webhook_data)
            elif webhook_type == "message_status":
                return self._process_status_webhook(config, webhook_data)
            else:
                _logger.info(f"Unhandled webhook type: {webhook_type}")
                return True

        except Exception as e:
            _logger.error(f"Error processing WhatsApp webhook: {e}")
            return False

    def _verify_webhook_data(self, webhook_data):
        """Verify webhook data integrity"""
        required_fields = ["object", "entry"]
        return all(field in webhook_data for field in required_fields)

    def _process_message_webhook(self, config, webhook_data):
        """Process message webhook"""
        entries = webhook_data.get("entry", [])

        for entry in entries:
            messaging = entry.get("messaging", [])
            for message_data in messaging:
                # Create message record
                message = self.env["ofitec.whatsapp.message"].create_from_webhook(
                    message_data, config
                )

                if message:
                    # Process message content for actions
                    self._process_message_content(message)

        return True

    def _process_status_webhook(self, config, webhook_data):
        """Process message status webhook"""
        entries = webhook_data.get("entry", [])

        for entry in entries:
            messaging = entry.get("messaging", [])
            for status_data in messaging:
                message_id = status_data.get("message", {}).get("id")
                status = status_data.get("message", {}).get("status")

                if message_id and status:
                    # Update message status
                    message = self.env["ofitec.whatsapp.message"].search(
                        [("whatsapp_message_id", "=", message_id)], limit=1
                    )

                    if message:
                        status_mapping = {
                            "delivered": "delivered",
                            "read": "read",
                            "failed": "failed",
                        }

                        if status in status_mapping:
                            message.write(
                                {
                                    status_mapping[status] + "_date": datetime.now(),
                                    "status": status_mapping[status],
                                }
                            )

        return True

    def _process_message_content(self, message):
        """Process message content and take actions"""
        if not message.content:
            return

        content = message.content.lower().strip()

        # Simple command processing
        if content in ["ok", "entendido", "confirmado", "aceptar"]:
            # Mark related action as acknowledged
            if message.next_action_id:
                message.next_action_id.write({"status": "in_progress"})
                # Send confirmation
                self._send_confirmation_message(message)

        elif content in ["completado", "terminado", "listo", "done"]:
            # Mark action as completed
            if message.next_action_id:
                message.next_action_id.write(
                    {"status": "completed", "completed_date": datetime.now()}
                )
                self._send_completion_message(message)

        elif content in ["cancelar", "cancel", "rechazar"]:
            # Cancel action
            if message.next_action_id:
                message.next_action_id.write({"status": "cancelled"})
                self._send_cancellation_message(message)

    def _send_confirmation_message(self, message):
        """Send confirmation message"""
        config = message.config_id
        confirmation_text = "✅ Acción confirmada. Gracias por tu respuesta."

        config.send_message(message.from_phone, confirmation_text)

    def _send_completion_message(self, message):
        """Send completion confirmation"""
        config = message.config_id
        completion_text = "🎉 Acción completada exitosamente. ¡Excelente trabajo!"

        config.send_message(message.from_phone, completion_text)

    def _send_cancellation_message(self, message):
        """Send cancellation confirmation"""
        config = message.config_id
        cancellation_text = "❌ Acción cancelada. Si necesitas ayuda, avísanos."

        config.send_message(message.from_phone, cancellation_text)
