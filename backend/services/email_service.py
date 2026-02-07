"""
Email Service - Transactional Emails
Supports SMTP (any provider) with HTML templates
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import logging
import secrets
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', SMTP_USER)
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'DigiForge')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'

APP_URL = os.environ.get('APP_URL', 'https://localhost:3000')


class EmailService:
    """Transactional email service"""
    
    def __init__(self):
        self.enabled = EMAIL_ENABLED and SMTP_USER and SMTP_PASSWORD
        if self.enabled:
            logger.info(f"Email service enabled via {SMTP_HOST}")
        else:
            logger.info("Email service disabled (set EMAIL_ENABLED=true and SMTP credentials)")
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": SMTP_HOST if self.enabled else None
        }
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email via SMTP"""
        if not self.enabled:
            logger.info(f"Email disabled - would send to {to_email}: {subject}")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
            msg["To"] = to_email
            
            # Plain text fallback
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            
            # HTML content
            msg.attach(MIMEText(html_content, "html"))
            
            # Connect and send
            if SMTP_USE_TLS:
                context = ssl.create_default_context()
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    server.starttls(context=context)
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
            else:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Email send failed to {to_email}: {e}")
            return False
    
    # ==================== EMAIL TEMPLATES ====================
    
    def _base_template(self, content: str) -> str:
        """Base HTML template wrapper"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
        .card {{ background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .logo {{ font-size: 24px; font-weight: bold; color: #6366f1; margin-bottom: 30px; }}
        .btn {{ display: inline-block; background: #6366f1; color: white !important; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
        .btn:hover {{ background: #5558e3; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #888; font-size: 13px; }}
        .highlight {{ background: #f0f0ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        h1 {{ color: #1a1a1a; margin-top: 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">DigiForge</div>
            {content}
            <div class="footer">
                <p>DigiForge - AI-Powered Digital Products</p>
                <p>This is an automated message. Please do not reply directly to this email.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    # ==================== TRANSACTIONAL EMAILS ====================
    
    async def send_welcome_email(self, to_email: str, name: str) -> bool:
        """Send welcome email after registration"""
        content = f"""
<h1>Welcome to DigiForge, {name}!</h1>
<p>Your account has been created successfully. You're ready to start creating AI-powered digital products.</p>

<div class="highlight">
    <strong>Your Free Plan includes:</strong>
    <ul>
        <li>10 credits to generate products</li>
        <li>Access to all product types (eBooks, Guides, Courses, Templates)</li>
        <li>Campaign Builder for marketing materials</li>
    </ul>
</div>

<p>
    <a href="{APP_URL}/dashboard" class="btn">Go to Dashboard</a>
</p>

<p>Need more credits? Upgrade to a paid plan anytime from your settings.</p>
"""
        return self._send_email(
            to_email,
            "Welcome to DigiForge! 🚀",
            self._base_template(content),
            f"Welcome to DigiForge, {name}! Your account is ready. Visit {APP_URL}/dashboard to get started."
        )
    
    async def send_payment_success_email(
        self, 
        to_email: str, 
        name: str, 
        plan_name: str, 
        amount: float, 
        credits: int,
        transaction_id: str
    ) -> bool:
        """Send payment confirmation email"""
        content = f"""
<h1>Payment Confirmed! ✓</h1>
<p>Hi {name},</p>
<p>Thank you for your purchase! Your payment has been processed successfully.</p>

<div class="highlight">
    <strong>Order Details:</strong>
    <table style="width: 100%; margin-top: 10px;">
        <tr><td>Plan:</td><td><strong>{plan_name}</strong></td></tr>
        <tr><td>Amount:</td><td><strong>€{amount:.2f}</strong></td></tr>
        <tr><td>Credits Added:</td><td><strong>{credits}</strong></td></tr>
        <tr><td>Transaction ID:</td><td style="font-family: monospace; font-size: 12px;">{transaction_id}</td></tr>
        <tr><td>Date:</td><td>{datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}</td></tr>
    </table>
</div>

<p>Your credits have been added to your account and are ready to use.</p>

<p>
    <a href="{APP_URL}/dashboard" class="btn">Start Creating</a>
</p>
"""
        return self._send_email(
            to_email,
            f"Payment Confirmed - {plan_name} Plan",
            self._base_template(content),
            f"Payment confirmed! {plan_name} plan - €{amount:.2f}. {credits} credits added. Transaction: {transaction_id}"
        )
    
    async def send_password_reset_email(self, to_email: str, name: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{APP_URL}/reset-password?token={reset_token}"
        content = f"""
<h1>Reset Your Password</h1>
<p>Hi {name},</p>
<p>We received a request to reset your password. Click the button below to create a new password:</p>

<p>
    <a href="{reset_url}" class="btn">Reset Password</a>
</p>

<p style="color: #888; font-size: 14px;">This link will expire in 1 hour.</p>

<p>If you didn't request this, you can safely ignore this email. Your password will not be changed.</p>

<p style="font-size: 13px; color: #888;">
    If the button doesn't work, copy and paste this URL into your browser:<br>
    <span style="word-break: break-all;">{reset_url}</span>
</p>
"""
        return self._send_email(
            to_email,
            "Reset Your Password - DigiForge",
            self._base_template(content),
            f"Reset your password: {reset_url} (expires in 1 hour)"
        )
    
    async def send_credits_low_email(self, to_email: str, name: str, remaining_credits: int) -> bool:
        """Send low credits warning email"""
        content = f"""
<h1>Running Low on Credits</h1>
<p>Hi {name},</p>
<p>You have <strong>{remaining_credits} credits</strong> remaining in your DigiForge account.</p>

<p>To continue creating products without interruption, consider upgrading your plan.</p>

<p>
    <a href="{APP_URL}/settings" class="btn">Upgrade Plan</a>
</p>
"""
        return self._send_email(
            to_email,
            f"Low Credits Warning - {remaining_credits} remaining",
            self._base_template(content),
            f"You have {remaining_credits} credits remaining. Upgrade at {APP_URL}/settings"
        )
    
    async def send_subscription_cancelled_email(self, to_email: str, name: str, end_date: str) -> bool:
        """Send subscription cancellation email"""
        content = f"""
<h1>Subscription Cancelled</h1>
<p>Hi {name},</p>
<p>Your DigiForge subscription has been cancelled.</p>

<div class="highlight">
    <p>Your current plan will remain active until: <strong>{end_date}</strong></p>
    <p>After this date, your account will revert to the Free plan with 10 credits.</p>
</div>

<p>We're sorry to see you go! If you change your mind, you can resubscribe anytime.</p>

<p>
    <a href="{APP_URL}/settings" class="btn">Resubscribe</a>
</p>
"""
        return self._send_email(
            to_email,
            "Subscription Cancelled - DigiForge",
            self._base_template(content),
            f"Your subscription has been cancelled. Active until {end_date}."
        )


# Global instance
email_service = EmailService()


def get_status() -> Dict[str, Any]:
    return email_service.get_status()


# Password reset token helpers
def generate_reset_token() -> str:
    """Generate secure reset token"""
    return secrets.token_urlsafe(32)


def token_expiry() -> str:
    """Get token expiry timestamp (1 hour from now)"""
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
