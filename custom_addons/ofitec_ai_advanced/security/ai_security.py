# -*- coding: utf-8 -*-
"""
Security configuration for Advanced AI Module
Defines access rights, record rules, and API security
"""

from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import AccessError


def check_ai_access(env, user_id):
    """Check if user has access to AI features"""
    if user_id == SUPERUSER_ID:
        return True

    user = env['res.users'].browse(user_id)

    # Check if user has AI access group
    ai_group = env.ref('ofitec_ai_advanced.group_ai_user', raise_if_not_found=False)
    if ai_group and ai_group in user.groups_id:
        return True

    # Check if user has manager access
    manager_group = env.ref('ofitec_ai_advanced.group_ai_manager', raise_if_not_found=False)
    if manager_group and manager_group in user.groups_id:
        return True

    return False


def check_ai_admin_access(env, user_id):
    """Check if user has admin access to AI features"""
    if user_id == SUPERUSER_ID:
        return True

    user = env['res.users'].browse(user_id)

    # Check if user has AI admin group
    admin_group = env.ref('ofitec_ai_advanced.group_ai_admin', raise_if_not_found=False)
    if admin_group and admin_group in user.groups_id:
        return True

    return False


class IrModelAccess(models.Model):
    """Extend model access control for AI features"""

    _inherit = 'ir.model.access'

    @api.model
    def check(self, model_name, mode='read', raise_exception=True):
        """Override check to add AI-specific access control"""
        # Call parent check first
        super(IrModelAccess, self).check(model_name, mode, raise_exception)

        # Additional checks for AI models
        if model_name.startswith('ofitec.ai'):
            user_id = self.env.user.id

            if not check_ai_access(self.env, user_id):
                if raise_exception:
                    raise AccessError("Access denied. AI features require specific permissions.")
                return False

            # Admin-only operations
            if mode in ['write', 'unlink'] and model_name in [
                'ofitec.ai.analytics',
                'ofitec.ai.api'
            ]:
                if not check_ai_admin_access(self.env, user_id):
                    if raise_exception:
                        raise AccessError("Admin access required for this operation.")
                    return False

        return True


class ResUsers(models.Model):
    """Extend users model with AI-specific methods"""

    _inherit = 'res.users'

    def _generate_api_token(self):
        """Generate API token for user"""
        import secrets
        import hashlib
        import time

        # Generate random token
        token_data = f"{self.id}:{secrets.token_hex(32)}:{int(time.time())}"
        token_hash = hashlib.sha256(token_data.encode()).hexdigest()

        # Store token (in production, use proper token storage)
        self.write({
            'api_token': token_hash,
            'api_token_expires': time.time() + 3600  # 1 hour
        })

        return token_hash

    api_token = fields.Char(string='API Token', readonly=True)
    api_token_expires = fields.Float(string='Token Expires', readonly=True)


class AIAPIAccessLog(models.Model):
    """Log API access for security monitoring"""

    _name = 'ofitec.ai.access_log'
    _description = 'AI API Access Log'
    _rec_name = 'access_time'

    user_id = fields.Many2one('res.users', string='User', required=True)
    endpoint = fields.Char(string='API Endpoint', required=True)
    method = fields.Char(string='HTTP Method', required=True)
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')
    access_time = fields.Datetime(string='Access Time', default=fields.Datetime.now)
    response_status = fields.Integer(string='Response Status')
    response_time = fields.Float(string='Response Time (ms)')
    request_size = fields.Integer(string='Request Size (bytes)')
    response_size = fields.Integer(string='Response Size (bytes)')
    error_message = fields.Text(string='Error Message')

    @api.model
    def log_access(self, user_id, endpoint, method, ip_address=None,
                   user_agent=None, response_status=200, response_time=0,
                   request_size=0, response_size=0, error_message=None):
        """Log API access"""
        self.create({
            'user_id': user_id,
            'endpoint': endpoint,
            'method': method,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'response_status': response_status,
            'response_time': response_time,
            'request_size': request_size,
            'response_size': response_size,
            'error_message': error_message
        })


class AIWebhookSecurity(models.Model):
    """Security configuration for webhooks"""

    _name = 'ofitec.ai.webhook_security'
    _description = 'AI Webhook Security Configuration'

    name = fields.Char(string='Webhook Name', required=True)
    service = fields.Selection([
        ('powerbi', 'Power BI'),
        ('tableau', 'Tableau'),
        ('slack', 'Slack'),
        ('custom', 'Custom')
    ], string='Service', required=True)

    webhook_url = fields.Char(string='Webhook URL', required=True)
    secret_token = fields.Char(string='Secret Token', required=True)
    is_active = fields.Boolean(string='Active', default=True)

    # Security settings
    ip_whitelist = fields.Text(string='IP Whitelist',
                              help='Comma-separated list of allowed IP addresses')
    rate_limit = fields.Integer(string='Rate Limit', default=100,
                               help='Maximum requests per hour')
    require_signature = fields.Boolean(string='Require Signature', default=True)

    # Monitoring
    last_request = fields.Datetime(string='Last Request')
    request_count = fields.Integer(string='Request Count', default=0)
    error_count = fields.Integer(string='Error Count', default=0)

    def validate_webhook_request(self, request_data, headers, remote_addr):
        """Validate incoming webhook request"""
        self.ensure_one()

        # Check if webhook is active
        if not self.is_active:
            return False, "Webhook is not active"

        # Check IP whitelist
        if self.ip_whitelist:
            allowed_ips = [ip.strip() for ip in self.ip_whitelist.split(',')]
            if remote_addr not in allowed_ips:
                return False, f"IP {remote_addr} not in whitelist"

        # Validate signature if required
        if self.require_signature:
            signature = headers.get('X-Webhook-Signature')
            if not signature:
                return False, "Missing webhook signature"

            # Verify signature (simplified - use proper HMAC in production)
            expected_signature = self._generate_signature(request_data)
            if signature != expected_signature:
                return False, "Invalid webhook signature"

        # Check rate limit
        if self._check_rate_limit():
            return False, "Rate limit exceeded"

        return True, "Valid"

    def _generate_signature(self, data):
        """Generate webhook signature"""
        import hmac
        import hashlib
        import json

        payload = json.dumps(data, sort_keys=True)
        signature = hmac.new(
            self.secret_token.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _check_rate_limit(self):
        """Check if rate limit is exceeded"""
        import time

        # Reset counter if hour has passed
        if self.last_request:
            time_diff = time.time() - self.last_request.timestamp()
            if time_diff > 3600:  # 1 hour
                self.request_count = 0

        if self.request_count >= self.rate_limit:
            return True

        self.request_count += 1
        self.last_request = fields.Datetime.now()
        return False

    def log_webhook_request(self, success=True, error_message=None):
        """Log webhook request"""
        if not success:
            self.error_count += 1
        else:
            self.request_count += 1

        self.last_request = fields.Datetime.now()


class AIEncryption(models.Model):
    """Encryption utilities for AI data"""

    _name = 'ofitec.ai.encryption'
    _description = 'AI Data Encryption Utilities'

    @api.model
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        from cryptography.fernet import Fernet
        import base64

        # Get encryption key (in production, use proper key management)
        key = self._get_encryption_key()
        f = Fernet(key)

        if isinstance(data, str):
            data = data.encode()

        encrypted = f.encrypt(data)
        return base64.b64encode(encrypted).decode()

    @api.model
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        from cryptography.fernet import Fernet
        import base64

        key = self._get_encryption_key()
        f = Fernet(key)

        try:
            decrypted = f.decrypt(base64.b64decode(encrypted_data))
            return decrypted.decode()
        except Exception:
            return None

    def _get_encryption_key(self):
        """Get encryption key (simplified - use proper key management)"""
        import os

        # In production, store key securely (e.g., AWS KMS, HashiCorp Vault)
        key = os.environ.get('ODOO_AI_ENCRYPTION_KEY')
        if not key:
            # Generate a key (store this securely!)
            from cryptography.fernet import Fernet
            key = Fernet.generate_key().decode()

        return key.encode()


class AISecurityAudit(models.Model):
    """Security audit trail for AI operations"""

    _name = 'ofitec.ai.security_audit'
    _description = 'AI Security Audit Trail'
    _rec_name = 'operation_time'

    user_id = fields.Many2one('res.users', string='User', required=True)
    operation = fields.Char(string='Operation', required=True)
    resource = fields.Char(string='Resource', required=True)
    operation_time = fields.Datetime(string='Operation Time', default=fields.Datetime.now)
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')
    success = fields.Boolean(string='Success', default=True)
    details = fields.Text(string='Details')

    @api.model
    def log_security_event(self, user_id, operation, resource, success=True,
                          ip_address=None, user_agent=None, details=None):
        """Log security event"""
        self.create({
            'user_id': user_id,
            'operation': operation,
            'resource': resource,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'details': details
        })
