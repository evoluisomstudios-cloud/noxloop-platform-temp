"""
Security Service - Rate Limiting and Anti-Abuse Protection
"""
import os
import time
import hashlib
from collections import defaultdict
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'

# Limits per window (in seconds)
RATE_LIMITS = {
    "register": {"requests": 5, "window": 3600},      # 5 registrations per hour per IP
    "login": {"requests": 10, "window": 900},          # 10 logins per 15 min per IP
    "login_failed": {"requests": 5, "window": 900},    # 5 failed logins = lockout
    "generate": {"requests": 30, "window": 3600},      # 30 generations per hour per user
    "api_global": {"requests": 100, "window": 60},     # 100 requests per minute per IP
    "password_reset": {"requests": 3, "window": 3600}, # 3 reset requests per hour
}

# Credit usage limits (anti-abuse)
MAX_CREDITS_PER_DAY = int(os.environ.get('MAX_CREDITS_PER_DAY', '100'))
MAX_GENERATIONS_PER_HOUR = int(os.environ.get('MAX_GENERATIONS_PER_HOUR', '20'))


class RateLimiter:
    """In-memory rate limiter (use Redis for distributed systems)"""
    
    def __init__(self):
        self.enabled = RATE_LIMIT_ENABLED
        self._requests: Dict[str, list] = defaultdict(list)
        self._blocked: Dict[str, float] = {}  # IP -> block until timestamp
        logger.info(f"Rate limiter {'enabled' if self.enabled else 'disabled'}")
    
    def _cleanup_old_requests(self, key: str, window: int):
        """Remove requests older than window"""
        cutoff = time.time() - window
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
    
    def _get_key(self, action: str, identifier: str) -> str:
        """Generate rate limit key"""
        return f"{action}:{hashlib.md5(identifier.encode()).hexdigest()[:16]}"
    
    def is_blocked(self, ip: str) -> bool:
        """Check if IP is temporarily blocked"""
        if ip in self._blocked:
            if time.time() < self._blocked[ip]:
                return True
            del self._blocked[ip]
        return False
    
    def block_ip(self, ip: str, duration_seconds: int = 3600):
        """Block an IP temporarily"""
        self._blocked[ip] = time.time() + duration_seconds
        logger.warning(f"IP blocked: {ip[:16]}... for {duration_seconds}s")
    
    def check_rate_limit(self, action: str, identifier: str) -> Dict[str, Any]:
        """
        Check if action is rate limited.
        Returns: {"allowed": bool, "remaining": int, "reset_at": float}
        """
        if not self.enabled:
            return {"allowed": True, "remaining": 999, "reset_at": 0}
        
        limit_config = RATE_LIMITS.get(action, RATE_LIMITS["api_global"])
        max_requests = limit_config["requests"]
        window = limit_config["window"]
        
        key = self._get_key(action, identifier)
        self._cleanup_old_requests(key, window)
        
        current_requests = len(self._requests[key])
        allowed = current_requests < max_requests
        
        # Calculate reset time
        if self._requests[key]:
            oldest = min(self._requests[key])
            reset_at = oldest + window
        else:
            reset_at = time.time() + window
        
        return {
            "allowed": allowed,
            "remaining": max(0, max_requests - current_requests - 1),
            "reset_at": reset_at,
            "current": current_requests
        }
    
    def record_request(self, action: str, identifier: str):
        """Record a request for rate limiting"""
        if not self.enabled:
            return
        
        key = self._get_key(action, identifier)
        self._requests[key].append(time.time())
    
    def record_failed_login(self, ip: str):
        """Record failed login attempt"""
        result = self.check_rate_limit("login_failed", ip)
        self.record_request("login_failed", ip)
        
        if not result["allowed"]:
            # Block IP for 30 minutes after too many failed attempts
            self.block_ip(ip, 1800)
            return False
        return True
    
    def clear_failed_logins(self, ip: str):
        """Clear failed login attempts after successful login"""
        key = self._get_key("login_failed", ip)
        self._requests[key] = []


class CreditProtection:
    """Anti-abuse credit usage protection"""
    
    def __init__(self):
        self._daily_usage: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "date": ""})
        self._hourly_usage: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "hour": ""})
    
    def check_credit_abuse(self, user_id: str) -> Dict[str, Any]:
        """Check if user is abusing credits"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        current_hour = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
        
        # Reset daily counter if new day
        if self._daily_usage[user_id]["date"] != today:
            self._daily_usage[user_id] = {"count": 0, "date": today}
        
        # Reset hourly counter if new hour
        if self._hourly_usage[user_id]["hour"] != current_hour:
            self._hourly_usage[user_id] = {"count": 0, "hour": current_hour}
        
        daily_count = self._daily_usage[user_id]["count"]
        hourly_count = self._hourly_usage[user_id]["count"]
        
        # Check limits
        if daily_count >= MAX_CREDITS_PER_DAY:
            return {
                "allowed": False,
                "reason": f"Daily credit limit reached ({MAX_CREDITS_PER_DAY}). Try again tomorrow.",
                "daily_remaining": 0,
                "hourly_remaining": max(0, MAX_GENERATIONS_PER_HOUR - hourly_count)
            }
        
        if hourly_count >= MAX_GENERATIONS_PER_HOUR:
            return {
                "allowed": False,
                "reason": f"Hourly generation limit reached ({MAX_GENERATIONS_PER_HOUR}). Try again in an hour.",
                "daily_remaining": MAX_CREDITS_PER_DAY - daily_count,
                "hourly_remaining": 0
            }
        
        return {
            "allowed": True,
            "reason": None,
            "daily_remaining": MAX_CREDITS_PER_DAY - daily_count - 1,
            "hourly_remaining": MAX_GENERATIONS_PER_HOUR - hourly_count - 1
        }
    
    def record_credit_usage(self, user_id: str, credits: int = 1):
        """Record credit usage"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        current_hour = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
        
        # Initialize if needed
        if self._daily_usage[user_id]["date"] != today:
            self._daily_usage[user_id] = {"count": 0, "date": today}
        if self._hourly_usage[user_id]["hour"] != current_hour:
            self._hourly_usage[user_id] = {"count": 0, "hour": current_hour}
        
        self._daily_usage[user_id]["count"] += credits
        self._hourly_usage[user_id]["count"] += credits


# Global instances
rate_limiter = RateLimiter()
credit_protection = CreditProtection()


def get_client_ip(request) -> str:
    """Extract client IP from request"""
    # Check X-Forwarded-For header (when behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to client host
    return request.client.host if request.client else "unknown"


def get_status() -> Dict[str, Any]:
    return {
        "rate_limiting_enabled": rate_limiter.enabled,
        "max_credits_per_day": MAX_CREDITS_PER_DAY,
        "max_generations_per_hour": MAX_GENERATIONS_PER_HOUR
    }
