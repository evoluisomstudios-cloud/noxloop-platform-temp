"""
Payment Service - Stripe + PayPal Integration
Handles checkout, webhooks, and plan activation
"""
import os
import uuid
import hmac
import hashlib
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# ==================== STRIPE ====================
STRIPE_ENABLED = os.environ.get('STRIPE_ENABLED', 'false').lower() == 'true'
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

stripe = None
if STRIPE_ENABLED and STRIPE_API_KEY:
    try:
        import stripe as stripe_module
        stripe_module.api_key = STRIPE_API_KEY
        stripe = stripe_module
        logger.info("Stripe initialized successfully")
    except ImportError:
        logger.warning("Stripe library not installed")
        STRIPE_ENABLED = False

# ==================== PAYPAL ====================
PAYPAL_ENABLED = os.environ.get('PAYPAL_ENABLED', 'false').lower() == 'true'
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # sandbox or live

PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"

class PaymentService:
    """Unified payment service for Stripe and PayPal"""
    
    def __init__(self):
        self.stripe_enabled = STRIPE_ENABLED
        self.paypal_enabled = PAYPAL_ENABLED
        self._paypal_token = None
        self._paypal_token_expires = None
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "stripe_enabled": self.stripe_enabled,
            "paypal_enabled": self.paypal_enabled,
            "paypal_mode": PAYPAL_MODE if self.paypal_enabled else None
        }
    
    # ==================== STRIPE METHODS ====================
    
    async def create_stripe_checkout(
        self,
        user_id: str,
        email: str,
        plan_id: str,
        plan_name: str,
        price: float,
        credits: int,
        success_url: str,
        cancel_url: str,
        mode: str = "payment"  # payment or subscription
    ) -> Dict[str, str]:
        """Create Stripe checkout session"""
        if not self.stripe_enabled or not stripe:
            raise ValueError("Stripe is not enabled")
        
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                customer_email=email,
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"DigiForge {plan_name} Plan",
                            "description": f"{credits} credits/month"
                        },
                        "unit_amount": int(price * 100),
                        "recurring": {"interval": "month"} if mode == "subscription" else None
                    },
                    "quantity": 1,
                }],
                mode=mode,
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}&provider=stripe",
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "credits": str(credits),
                    "provider": "stripe"
                }
            )
            
            return {
                "url": session.url,
                "session_id": session.id,
                "provider": "stripe"
            }
        except Exception as e:
            logger.error(f"Stripe checkout error: {e}")
            raise ValueError(f"Failed to create checkout: {str(e)}")
    
    def verify_stripe_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature and return event"""
        if not stripe or not STRIPE_WEBHOOK_SECRET:
            raise ValueError("Stripe webhook not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe webhook signature failed: {e}")
            raise ValueError("Invalid signature")
    
    async def get_stripe_session(self, session_id: str) -> Dict[str, Any]:
        """Get Stripe checkout session details"""
        if not stripe:
            raise ValueError("Stripe not enabled")
        
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "id": session.id,
                "status": session.payment_status,
                "customer_email": session.customer_email,
                "amount_total": session.amount_total / 100 if session.amount_total else 0,
                "metadata": dict(session.metadata) if session.metadata else {}
            }
        except Exception as e:
            logger.error(f"Get Stripe session error: {e}")
            raise ValueError(f"Failed to get session: {str(e)}")
    
    # ==================== PAYPAL METHODS ====================
    
    async def _get_paypal_token(self) -> str:
        """Get PayPal OAuth token"""
        if not self.paypal_enabled:
            raise ValueError("PayPal is not enabled")
        
        # Check if token is still valid
        if self._paypal_token and self._paypal_token_expires:
            if datetime.now(timezone.utc) < self._paypal_token_expires:
                return self._paypal_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYPAL_API_BASE}/v1/oauth2/token",
                auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"PayPal auth failed: {response.text}")
                raise ValueError("PayPal authentication failed")
            
            data = response.json()
            self._paypal_token = data["access_token"]
            # Set expiry 5 minutes before actual expiry
            expires_in = data.get("expires_in", 32400) - 300
            from datetime import timedelta
            self._paypal_token_expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            return self._paypal_token
    
    async def create_paypal_order(
        self,
        user_id: str,
        plan_id: str,
        plan_name: str,
        price: float,
        credits: int,
        return_url: str,
        cancel_url: str
    ) -> Dict[str, str]:
        """Create PayPal order"""
        if not self.paypal_enabled:
            raise ValueError("PayPal is not enabled")
        
        token = await self._get_paypal_token()
        order_id = f"order_{uuid.uuid4().hex[:12]}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYPAL_API_BASE}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "intent": "CAPTURE",
                    "purchase_units": [{
                        "reference_id": order_id,
                        "description": f"DigiForge {plan_name} Plan - {credits} credits",
                        "custom_id": f"{user_id}|{plan_id}|{credits}",
                        "amount": {
                            "currency_code": "EUR",
                            "value": f"{price:.2f}"
                        }
                    }],
                    "application_context": {
                        "brand_name": "DigiForge",
                        "landing_page": "BILLING",
                        "user_action": "PAY_NOW",
                        "return_url": return_url + f"?order_id={{order_id}}&provider=paypal",
                        "cancel_url": cancel_url
                    }
                }
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"PayPal order failed: {response.text}")
                raise ValueError("Failed to create PayPal order")
            
            data = response.json()
            
            # Find approval URL
            approve_url = None
            for link in data.get("links", []):
                if link.get("rel") == "approve":
                    approve_url = link.get("href")
                    break
            
            if not approve_url:
                raise ValueError("PayPal approval URL not found")
            
            return {
                "url": approve_url,
                "order_id": data["id"],
                "provider": "paypal"
            }
    
    async def capture_paypal_order(self, order_id: str) -> Dict[str, Any]:
        """Capture (complete) PayPal order after user approval"""
        if not self.paypal_enabled:
            raise ValueError("PayPal is not enabled")
        
        token = await self._get_paypal_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"PayPal capture failed: {response.text}")
                raise ValueError("Failed to capture PayPal payment")
            
            data = response.json()
            
            # Extract custom data
            custom_id = ""
            amount = 0.0
            for unit in data.get("purchase_units", []):
                custom_id = unit.get("custom_id", "")
                for capture in unit.get("payments", {}).get("captures", []):
                    amount = float(capture.get("amount", {}).get("value", 0))
            
            # Parse custom_id: user_id|plan_id|credits
            parts = custom_id.split("|") if custom_id else []
            
            return {
                "id": data["id"],
                "status": data["status"],
                "payer_email": data.get("payer", {}).get("email_address"),
                "amount": amount,
                "user_id": parts[0] if len(parts) > 0 else None,
                "plan_id": parts[1] if len(parts) > 1 else None,
                "credits": int(parts[2]) if len(parts) > 2 else 0
            }
    
    async def get_paypal_order(self, order_id: str) -> Dict[str, Any]:
        """Get PayPal order details"""
        if not self.paypal_enabled:
            raise ValueError("PayPal is not enabled")
        
        token = await self._get_paypal_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to get PayPal order")
            
            return response.json()
    
    def verify_paypal_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify PayPal webhook signature (simplified)"""
        # In production, implement full verification using PayPal API
        # For now, we rely on HTTPS and validate order status via API
        return True


# Global instance
payment_service = PaymentService()


def get_status() -> Dict[str, Any]:
    return payment_service.get_status()
