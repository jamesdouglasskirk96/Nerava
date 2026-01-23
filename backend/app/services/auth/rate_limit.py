"""
Rate limiting service for OTP authentication
In-memory implementation, structured for Redis migration
"""
import time
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimitEntry:
    """Rate limit entry for a phone or IP"""
    
    def __init__(self):
        self.attempts: list[float] = []  # Timestamps of attempts
        self.last_success: Optional[float] = None  # Timestamp of last success
        self.locked_until: Optional[float] = None  # Timestamp when lockout expires


class RateLimitService:
    """
    Rate limiting service for OTP authentication.
    
    Limits:
    - start: max 3 / 10 min per phone, max 3 / 10 min per IP
    - verify: max 6 attempts / 10 min per phone
    - Cooldown: 30s after successful verify before resend allowed
    - Lockout: 15 min after too many verify failures (per phone)
    """
    
    # Rate limits (relaxed for development - TODO: tighten for production)
    START_LIMIT_PHONE = 100  # Max start requests per phone per window
    START_LIMIT_IP = 100  # Max start requests per IP per window
    START_WINDOW_SECONDS = 60  # 1 minute

    VERIFY_LIMIT_PHONE = 100  # Max verify attempts per phone per window
    VERIFY_WINDOW_SECONDS = 60  # 1 minute

    COOLDOWN_SECONDS = 5  # 5 seconds cooldown after success
    LOCKOUT_SECONDS = 60  # 1 minute lockout after too many failures
    
    def __init__(self):
        # In-memory stores: phone -> RateLimitEntry, IP -> RateLimitEntry
        self._phone_limits: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._ip_limits: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._cleanup_interval = 3600  # Cleanup old entries every hour
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove old entries that are outside the rate limit windows"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_start = now - self.START_WINDOW_SECONDS
        cutoff_verify = now - self.VERIFY_WINDOW_SECONDS
        cutoff_lockout = now - self.LOCKOUT_SECONDS
        
        # Cleanup phone limits
        phones_to_remove = []
        for phone, entry in self._phone_limits.items():
            # Remove old attempts
            entry.attempts = [ts for ts in entry.attempts if ts > cutoff_verify]
            
            # Remove entry if no recent activity and not locked
            if (
                not entry.attempts
                and (not entry.last_success or entry.last_success < cutoff_start)
                and (not entry.locked_until or entry.locked_until < cutoff_lockout)
            ):
                phones_to_remove.append(phone)
        
        for phone in phones_to_remove:
            del self._phone_limits[phone]
        
        # Cleanup IP limits
        ips_to_remove = []
        for ip, entry in self._ip_limits.items():
            entry.attempts = [ts for ts in entry.attempts if ts > cutoff_start]
            
            if not entry.attempts and (not entry.last_success or entry.last_success < cutoff_start):
                ips_to_remove.append(ip)
        
        for ip in ips_to_remove:
            del self._ip_limits[ip]
        
        self._last_cleanup = now
    
    def check_rate_limit_start(self, phone: str, ip: str) -> Tuple[bool, Optional[str]]:
        """
        Check if OTP start request is allowed.
        
        Args:
            phone: Normalized phone number
            ip: Client IP address
            
        Returns:
            Tuple of (allowed, error_message)
        """
        self._cleanup_old_entries()
        now = time.time()
        
        # Check phone limit
        phone_entry = self._phone_limits[phone]
        
        # Check if locked out
        if phone_entry.locked_until and phone_entry.locked_until > now:
            remaining = int(phone_entry.locked_until - now)
            return False, f"Phone number is temporarily locked. Please try again in {remaining} seconds."
        
        # Check cooldown
        if phone_entry.last_success:
            cooldown_until = phone_entry.last_success + self.COOLDOWN_SECONDS
            if cooldown_until > now:
                remaining = int(cooldown_until - now)
                return False, f"Please wait {remaining} seconds before requesting a new code."
        
        # Count recent start attempts for phone
        window_start = now - self.START_WINDOW_SECONDS
        recent_phone_attempts = [ts for ts in phone_entry.attempts if ts > window_start]
        
        if len(recent_phone_attempts) >= self.START_LIMIT_PHONE:
            return False, "Too many OTP requests. Please wait before requesting a new code."
        
        # Check IP limit
        ip_entry = self._ip_limits[ip]
        recent_ip_attempts = [ts for ts in ip_entry.attempts if ts > window_start]
        
        if len(recent_ip_attempts) >= self.START_LIMIT_IP:
            return False, "Too many OTP requests from this IP. Please wait before requesting a new code."
        
        return True, None
    
    def record_start_attempt(self, phone: str, ip: str):
        """Record an OTP start attempt"""
        now = time.time()
        self._phone_limits[phone].attempts.append(now)
        self._ip_limits[ip].attempts.append(now)
    
    def check_rate_limit_verify(self, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Check if OTP verify attempt is allowed.
        
        Args:
            phone: Normalized phone number
            
        Returns:
            Tuple of (allowed, error_message)
        """
        self._cleanup_old_entries()
        now = time.time()
        
        phone_entry = self._phone_limits[phone]
        
        # Check if locked out
        if phone_entry.locked_until and phone_entry.locked_until > now:
            remaining = int(phone_entry.locked_until - now)
            return False, f"Phone number is temporarily locked. Please try again in {remaining} seconds."
        
        # Count recent verify attempts
        window_start = now - self.VERIFY_WINDOW_SECONDS
        recent_attempts = [ts for ts in phone_entry.attempts if ts > window_start]
        
        if len(recent_attempts) >= self.VERIFY_LIMIT_PHONE:
            # Lock out for 15 minutes
            phone_entry.locked_until = now + self.LOCKOUT_SECONDS
            return False, "Too many verification attempts. Phone number is temporarily locked."
        
        return True, None
    
    def record_verify_attempt(self, phone: str, success: bool):
        """
        Record an OTP verify attempt.
        
        Args:
            phone: Normalized phone number
            success: Whether verification was successful
        """
        now = time.time()
        phone_entry = self._phone_limits[phone]
        
        if success:
            # Record success and reset attempts
            phone_entry.last_success = now
            phone_entry.attempts = []  # Clear attempts on success
            phone_entry.locked_until = None  # Clear lockout
        else:
            # Record failed attempt
            phone_entry.attempts.append(now)
            
            # Check if we should lock out (after max attempts)
            window_start = now - self.VERIFY_WINDOW_SECONDS
            recent_attempts = [ts for ts in phone_entry.attempts if ts > window_start]
            
            if len(recent_attempts) >= self.VERIFY_LIMIT_PHONE:
                phone_entry.locked_until = now + self.LOCKOUT_SECONDS
    
    def is_locked_out(self, phone: str) -> bool:
        """Check if phone number is currently locked out"""
        self._cleanup_old_entries()
        now = time.time()
        phone_entry = self._phone_limits[phone]
        return phone_entry.locked_until is not None and phone_entry.locked_until > now


# Global singleton instance
_rate_limit_service: Optional[RateLimitService] = None


def get_rate_limit_service() -> RateLimitService:
    """Get or create rate limit service singleton"""
    global _rate_limit_service
    if _rate_limit_service is None:
        _rate_limit_service = RateLimitService()
    return _rate_limit_service




