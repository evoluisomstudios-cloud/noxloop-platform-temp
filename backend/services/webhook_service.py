"""
Webhook Service for n8n and external automation integrations
"""
import os
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class WebhookService:
    """Webhook service for sending events to n8n or other automation platforms"""
    
    def __init__(self):
        self.enabled = os.environ.get("N8N_WEBHOOK_ENABLED", "false").lower() == "true"
        self.webhook_url = os.environ.get("N8N_WEBHOOK_URL", "")
        self.timeout = float(os.environ.get("N8N_WEBHOOK_TIMEOUT", "10.0"))
        self.retry_count = int(os.environ.get("N8N_WEBHOOK_RETRIES", "2"))
        
        if self.enabled and self.webhook_url:
            logger.info(f"Webhooks enabled @ {self.webhook_url}")
        else:
            logger.info("Webhooks disabled")
    
    async def send_event(self, event_type: str, payload: Dict[str, Any], retry: bool = True) -> bool:
        """
        Send event to webhook endpoint.
        Returns True if successful, False otherwise.
        Never raises exceptions - fails silently to not break main flow.
        """
        if not self.enabled or not self.webhook_url:
            return False
        
        event_data = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }
        
        attempts = self.retry_count if retry else 1
        
        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.webhook_url,
                        json=event_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code in [200, 201, 202, 204]:
                        logger.info(f"Webhook sent: {event_type}")
                        return True
                    else:
                        logger.warning(f"Webhook {event_type} returned status {response.status_code}")
                        
            except Exception as e:
                logger.warning(f"Webhook {event_type} failed (attempt {attempt + 1}/{attempts}): {e}")
            
            if attempt < attempts - 1:
                await asyncio.sleep(1)  # Wait before retry
        
        return False
    
    # Convenience methods for common events
    async def campaign_created(self, campaign_id: str, workspace_id: str, user_id: str, campaign_type: str):
        """Send campaign_created event"""
        return await self.send_event("campaign_created", {
            "campaign_id": campaign_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "campaign_type": campaign_type
        })
    
    async def export_generated(self, export_id: str, workspace_id: str, user_id: str, export_type: str, file_size: int):
        """Send export_generated event"""
        return await self.send_event("export_generated", {
            "export_id": export_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "export_type": export_type,
            "file_size_bytes": file_size
        })
    
    async def payment_succeeded(self, payment_id: str, user_id: str, amount: float, currency: str, plan: str):
        """Send payment_succeeded event"""
        return await self.send_event("payment_succeeded", {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "plan": plan
        })
    
    async def user_registered(self, user_id: str, email: str, workspace_id: str):
        """Send user_registered event"""
        return await self.send_event("user_registered", {
            "user_id": user_id,
            "email": email,
            "workspace_id": workspace_id
        })
    
    def get_status(self) -> Dict[str, Any]:
        """Get webhook service status"""
        return {
            "enabled": self.enabled,
            "configured": bool(self.webhook_url) if self.enabled else False
        }

# Global instance
webhook_service = WebhookService()
