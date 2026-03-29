"""
POS Adapter Abstraction Layer

Platform-specific adapters for building ordering URLs, injecting discounts/phone,
and detecting order confirmation across Toast, Square, Shopify, and generic POS systems.

EXTENSIBILITY: Adding a new POS (WooCommerce, Clover, SpotOn) requires only:
  1. New adapter class implementing the 4 POSAdapter methods
  2. New pos_type enum value in the Merchant model
  3. Register in POSAdapterFactory.get_adapter()
No changes to WebView screen, merchant card, attribution logging, or cluster intelligence layer.
"""
import re
import logging
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

UTM_PARAMS = "utm_source=nerava&utm_medium=ev_session&utm_campaign=charging_verified"


class POSAdapter(ABC):
    """Base class for POS platform adapters."""

    @abstractmethod
    def build_ordering_url(
        self,
        ordering_url: str,
        session_id: str,
        user_phone: Optional[str] = None,
        discount_code: Optional[str] = None,
    ) -> str:
        """Build the full ordering URL with UTM tracking and discount params."""

    @abstractmethod
    def get_phone_inject_js(self, phone_number: str, custom_selector: Optional[str] = None) -> str:
        """Return JS snippet to inject phone number into the ordering page."""

    @abstractmethod
    def get_discount_inject_js(self, discount_code: str, custom_selector: Optional[str] = None) -> str:
        """Return JS snippet to inject discount code into the ordering page."""

    @abstractmethod
    def detect_order_confirmation(self, url: str, custom_pattern: Optional[str] = None) -> bool:
        """Check if the current URL matches an order confirmation page."""


class ToastAdapter(POSAdapter):
    """Adapter for Toast POS (order.toasttab.com)."""

    def build_ordering_url(self, ordering_url, session_id, user_phone=None, discount_code=None):
        sep = "&" if "?" in ordering_url else "?"
        url = f"{ordering_url}{sep}{UTM_PARAMS}&session_id={session_id}"
        return url

    def get_phone_inject_js(self, phone_number, custom_selector=None):
        selector = custom_selector or 'input[type="tel"]'
        return _build_inject_js(selector, phone_number)

    def get_discount_inject_js(self, discount_code, custom_selector=None):
        # Toast doesn't support URL-based discount injection; use promo code field
        selector = custom_selector or 'input[name="promoCode"], input[placeholder*="promo" i], input[placeholder*="coupon" i]'
        return _build_inject_js(selector, discount_code)

    def detect_order_confirmation(self, url, custom_pattern=None):
        if custom_pattern:
            return bool(re.search(custom_pattern, url))
        return bool(re.search(r"toasttab\.com/.*/confirm", url) or
                     re.search(r"toasttab\.com/.*/order-confirmation", url))


class SquareAdapter(POSAdapter):
    """Adapter for Square POS (square.site / squareup.com)."""

    def build_ordering_url(self, ordering_url, session_id, user_phone=None, discount_code=None):
        sep = "&" if "?" in ordering_url else "?"
        url = f"{ordering_url}{sep}{UTM_PARAMS}&session_id={session_id}"
        if discount_code:
            url += f"&discount={discount_code}"
        return url

    def get_phone_inject_js(self, phone_number, custom_selector=None):
        selector = custom_selector or 'input[name="phone"], input[type="tel"]'
        return _build_inject_js(selector, phone_number)

    def get_discount_inject_js(self, discount_code, custom_selector=None):
        selector = custom_selector or 'input[name="discount"], input[placeholder*="discount" i]'
        return _build_inject_js(selector, discount_code)

    def detect_order_confirmation(self, url, custom_pattern=None):
        if custom_pattern:
            return bool(re.search(custom_pattern, url))
        return bool(re.search(r"square\.site/.*/confirmation", url) or
                     re.search(r"squareup\.com/.*/receipt", url))


class ShopifyAdapter(POSAdapter):
    """Adapter for Shopify POS (myshopify.com / custom domains)."""

    def build_ordering_url(self, ordering_url, session_id, user_phone=None, discount_code=None):
        # Shopify uses /discount/{code} path before cart
        if discount_code:
            base = ordering_url.rstrip("/")
            url = f"{base}/discount/{discount_code}"
        else:
            url = ordering_url
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{UTM_PARAMS}&session_id={session_id}"
        return url

    def get_phone_inject_js(self, phone_number, custom_selector=None):
        selector = custom_selector or '#checkout_shipping_address_phone, input[autocomplete="tel"]'
        return _build_inject_js(selector, phone_number)

    def get_discount_inject_js(self, discount_code, custom_selector=None):
        selector = custom_selector or 'input[name="checkout[reduction_code]"], input[placeholder*="discount" i]'
        return _build_inject_js(selector, discount_code)

    def detect_order_confirmation(self, url, custom_pattern=None):
        if custom_pattern:
            return bool(re.search(custom_pattern, url))
        return bool(re.search(r"/thank_you", url) or
                     re.search(r"/orders/.*/confirm", url))


class OtherAdapter(POSAdapter):
    """Fallback adapter for unknown POS systems. Opens URL as-is, no injection."""

    def build_ordering_url(self, ordering_url, session_id, user_phone=None, discount_code=None):
        sep = "&" if "?" in ordering_url else "?"
        return f"{ordering_url}{sep}{UTM_PARAMS}&session_id={session_id}"

    def get_phone_inject_js(self, phone_number, custom_selector=None):
        if custom_selector:
            return _build_inject_js(custom_selector, phone_number)
        return ""  # No injection for unknown POS

    def get_discount_inject_js(self, discount_code, custom_selector=None):
        if custom_selector:
            return _build_inject_js(custom_selector, discount_code)
        return ""  # No injection for unknown POS

    def detect_order_confirmation(self, url, custom_pattern=None):
        if custom_pattern:
            return bool(re.search(custom_pattern, url))
        return False  # Manual confirmation via "I completed my order" button


class POSAdapterFactory:
    """Factory for creating POS adapters by platform type.

    EXTENSIBILITY: To add a new POS (WooCommerce, Clover, SpotOn):
      1. Create a new adapter class implementing the 4 POSAdapter methods
      2. Add a new pos_type enum value in the Merchant model
      3. Register it here in _ADAPTERS
    No changes needed in WebView screen, merchant card, attribution logging, or cluster layer.
    """

    _ADAPTERS = {
        "toast": ToastAdapter,
        "square": SquareAdapter,
        "shopify": ShopifyAdapter,
        "other": OtherAdapter,
    }

    @classmethod
    def get_adapter(cls, pos_type: Optional[str]) -> POSAdapter:
        adapter_cls = cls._ADAPTERS.get(pos_type or "other", OtherAdapter)
        return adapter_cls()


def _build_inject_js(selector: str, value: str) -> str:
    """Build a JS snippet that sets a value on the first matching element."""
    safe_value = value.replace("'", "\\'").replace('"', '\\"')
    safe_selector = selector.replace("'", "\\'")
    return f"""
    (function() {{
        var el = document.querySelector('{safe_selector}');
        if (el) {{
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(el, '{safe_value}');
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    }})();
    """.strip()
