# -*- coding: utf-8 -*-
"""
Integration between Next Action and WhatsApp modules
"""

import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class NextAction(models.Model):
    """Extend NextAction model to integrate with WhatsApp"""

    _inherit = 'ofitec.next.action'

    # WhatsApp Integration Fields
    whatsapp_enabled = fields.Boolean(string='Enable WhatsApp Notifications',
                                      default=True,
                                      help='Send WhatsApp notifications for this action')
    whatsapp_sent = fields.Boolean(string='WhatsApp Sent', readonly=True,
                                   help='Whether WhatsApp notification was sent')
    whatsapp_recipients = fields.Many2many('res.partner', string='WhatsApp Recipients',
                                           help='Contacts to notify via WhatsApp')

    @api.model
    def create(self, vals):
        """Override create to send WhatsApp notifications for urgent actions"""
        record = super(NextAction, self).create(vals)

        # Send WhatsApp notification if enabled and action is urgent
        if record.whatsapp_enabled and record.priority <= 2:
            try:
                record._send_whatsapp_notification()
            except Exception as e:
                _logger.error(f"Failed to send WhatsApp notification for action {record.id}: {e}")
                # Don't fail the creation, just log the error

        return record

    def write(self, vals):
        """Override write to send WhatsApp notifications when priority changes"""
        result = super(NextAction, self).write(vals)

        # Send notification if priority changed to urgent
        if 'priority' in vals and vals['priority'] <= 2:
            for record in self:
                if record.whatsapp_enabled and not record.whatsapp_sent:
                    try:
                        record._send_whatsapp_notification()
                    except Exception as e:
                        _logger.error(f"Failed to send WhatsApp notification for action {record.id}: {e}")

        return result

    def _send_whatsapp_notification(self):
        """Send WhatsApp notification for this action"""
        self.ensure_one()

        # Get active WhatsApp configuration
        try:
            whatsapp_config = self.env['ofitec.whatsapp.config'].get_active_config()
        except UserError:
            _logger.warning("No active WhatsApp configuration found")
            return

        # Get recipients
        recipients = self._get_whatsapp_recipients()
        if not recipients:
            _logger.info(f"No WhatsApp recipients found for action {self.id}")
            return

        # Prepare message
        message_text = self._prepare_whatsapp_message()

        # Send to each recipient
        success_count = 0
        for recipient in recipients:
            phone_number = recipient.mobile or recipient.phone
            if phone_number:
                # Format phone number (add + if missing)
                if not phone_number.startswith('+'):
                    phone_number = '+' + phone_number

                try:
                    result = whatsapp_config.send_message(phone_number, message_text)
                    if result['success']:
                        success_count += 1
                        _logger.info(f"WhatsApp notification sent to {phone_number} for action {self.id}")
                    else:
                        _logger.error(f"Failed to send WhatsApp to {phone_number}: {result['error']}")
                except Exception as e:
                    _logger.error(f"Error sending WhatsApp to {phone_number}: {e}")

        # Mark as sent if at least one message was successful
        if success_count > 0:
            self.write({
                'whatsapp_sent': True
            })

    def _get_whatsapp_recipients(self):
        """Get list of recipients for WhatsApp notifications"""
        self.ensure_one()

        recipients = []

        # Add explicit recipients
        if self.whatsapp_recipients:
            recipients.extend(self.whatsapp_recipients)

        # Add project manager if exists
        if self.project_id and self.project_id.user_id:
            recipients.append(self.project_id.user_id.partner_id)

        # Add assigned user if exists
        if self.user_id:
            recipients.append(self.user_id.partner_id)

        # Remove duplicates
        seen = set()
        unique_recipients = []
        for recipient in recipients:
            if recipient.id not in seen and recipient.mobile:
                seen.add(recipient.id)
                unique_recipients.append(recipient)

        return unique_recipients

    def _prepare_whatsapp_message(self):
        """Prepare WhatsApp message content"""
        self.ensure_one()

        priority_emojis = {
            1: '🚨',
            2: '⚡',
            3: '📋',
            4: '📝'
        }

        emoji = priority_emojis.get(self.priority, '📝')

        message = f"""{emoji} *ACCIÓN REQUERIDA - OFITEC*

🏗️ *Proyecto:* {self.project_id.name if self.project_id else 'General'}

📋 *Acción:* {self.name}

📝 *Descripción:* {self.description or 'Sin descripción'}

🔥 *Prioridad:* {'CRÍTICA' if self.priority == 1 else 'ALTA' if self.priority == 2 else 'MEDIA' if self.priority == 3 else 'BAJA'}

📅 *Fecha límite:* {self.deadline.strftime('%d/%m/%Y %H:%M') if self.deadline else 'Inmediata'}

💰 *Impacto estimado:* {self.expected_benefits or 'No especificado'}

*Responde con:*
✅ *OK* - Confirmar que iniciarás la acción
🎉 *COMPLETADO* - Si ya está terminada
❌ *CANCELAR* - Si no puedes realizarla

¡Gracias por tu atención inmediata! 🙏"""

        return message

    def send_whatsapp_reminder(self):
        """Send WhatsApp reminder for this action"""
        self.ensure_one()

        if not self.whatsapp_enabled:
            raise UserError("WhatsApp notifications are disabled for this action")

        try:
            self._send_whatsapp_notification()
            return {
                'success': True,
                'message': 'WhatsApp reminder sent successfully'
            }
        except Exception as e:
            _logger.error(f"Failed to send WhatsApp reminder: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def action_mark_completed_via_whatsapp(self):
        """Mark action as completed via WhatsApp response"""
        self.ensure_one()

        self.write({
            'status': 'completed',
            'completed_date': fields.Datetime.now()
        })

        # Send confirmation via WhatsApp
        try:
            whatsapp_config = self.env['ofitec.whatsapp.config'].get_active_config()
            recipients = self._get_whatsapp_recipients()

            confirmation_message = f"""🎉 *ACCIÓN COMPLETADA*

✅ La acción "{self.name}" ha sido marcada como completada.

📅 *Completada:* {self.completed_date.strftime('%d/%m/%Y %H:%M')}

¡Excelente trabajo! 👏"""

            for recipient in recipients:
                phone_number = recipient.mobile or recipient.phone
                if phone_number and not phone_number.startswith('+'):
                    phone_number = '+' + phone_number

                if phone_number:
                    whatsapp_config.send_message(phone_number, confirmation_message)

        except Exception as e:
            _logger.error(f"Failed to send completion confirmation: {e}")

    def action_confirm_via_whatsapp(self):
        """Confirm action via WhatsApp response"""
        self.ensure_one()

        self.write({
            'status': 'in_progress'
        })

        # Send confirmation
        try:
            whatsapp_config = self.env['ofitec.whatsapp.config'].get_active_config()
            recipients = self._get_whatsapp_recipients()

            confirmation_message = f"""✅ *ACCIÓN CONFIRMADA*

La acción "{self.name}" ha sido confirmada y está en progreso.

📋 *Estado:* En progreso
👤 *Responsable:* {self.user_id.name if self.user_id else 'Por asignar'}

Te notificaremos cuando esté completada."""

            for recipient in recipients:
                phone_number = recipient.mobile or recipient.phone
                if phone_number and not phone_number.startswith('+'):
                    phone_number = '+' + phone_number

                if phone_number:
                    whatsapp_config.send_message(phone_number, confirmation_message)

        except Exception as e:
            _logger.error(f"Failed to send confirmation: {e}")


class WhatsAppConfig(models.Model):
    """Extend WhatsApp config to integrate with Next Action"""

    _inherit = 'ofitec.whatsapp.config'

    # Integration settings
    auto_notify_urgent_actions = fields.Boolean(string='Auto-notify Urgent Actions',
                                                default=True,
                                                help='Automatically send WhatsApp notifications for urgent actions')
    notify_project_managers = fields.Boolean(string='Notify Project Managers',
                                             default=True,
                                             help='Send notifications to project managers')
    notify_team_leaders = fields.Boolean(string='Notify Team Leaders',
                                         default=False,
                                         help='Send notifications to team leaders')

    def send_urgent_action_notification(self, action):
        """Send WhatsApp notification for urgent action"""
        self.ensure_one()

        if not self.is_active or not self.auto_notify_urgent_actions:
            return

        # Use the action's method to send notification
        action._send_whatsapp_notification()
