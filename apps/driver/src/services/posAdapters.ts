/**
 * POS Adapter Abstraction Layer
 *
 * Platform-specific adapters for building ordering URLs, injecting discounts/phone,
 * and detecting order confirmation across Toast, Square, Shopify, and generic POS systems.
 *
 * EXTENSIBILITY: Adding a new POS (WooCommerce, Clover, SpotOn) requires only:
 *   1. New adapter file implementing the 4 POSAdapter methods
 *   2. New pos_type enum value
 *   3. Register in POSAdapterFactory.getAdapter()
 * No changes to WebView screen, merchant card, attribution logging, or cluster intelligence layer.
 */

export type POSType = 'toast' | 'square' | 'shopify' | 'other'

export interface MerchantOrderingConfig {
  ordering_enabled: boolean
  pos_type: POSType | null
  ordering_url: string | null
  discount_injection_method: 'url_param' | 'js_inject' | 'promo_code' | null
  discount_param_key: string | null
  phone_field_selector: string | null
  confirmation_url_pattern: string | null
  nerava_offer: string | null
  nerava_discount_code: string | null
}

const UTM_PARAMS = 'utm_source=nerava&utm_medium=ev_session&utm_campaign=charging_verified'

export interface POSAdapter {
  buildOrderingURL(
    orderingUrl: string,
    sessionId: string,
    userPhone?: string,
    discountCode?: string
  ): string

  getPhoneInjectJS(phoneNumber: string, customSelector?: string): string
  getDiscountInjectJS(discountCode: string, customSelector?: string): string
  detectOrderConfirmation(url: string, customPattern?: string): boolean
}

function buildInjectJS(selector: string, value: string): string {
  const safeValue = value.replace(/'/g, "\\'")
  const safeSelector = selector.replace(/'/g, "\\'")
  return `
    (function() {
      var el = document.querySelector('${safeSelector}');
      if (el) {
        var nativeSetter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeSetter.call(el, '${safeValue}');
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    })();
  `.trim()
}

// ─── Toast Adapter ──────────────────────────────────────────────────────────

const toastAdapter: POSAdapter = {
  buildOrderingURL(orderingUrl, sessionId, _userPhone, _discountCode) {
    const sep = orderingUrl.includes('?') ? '&' : '?'
    return `${orderingUrl}${sep}${UTM_PARAMS}&session_id=${sessionId}`
  },

  getPhoneInjectJS(phoneNumber, customSelector) {
    return buildInjectJS(customSelector || 'input[type="tel"]', phoneNumber)
  },

  getDiscountInjectJS(discountCode, customSelector) {
    return buildInjectJS(
      customSelector || 'input[name="promoCode"], input[placeholder*="promo" i], input[placeholder*="coupon" i]',
      discountCode
    )
  },

  detectOrderConfirmation(url, customPattern) {
    if (customPattern) return new RegExp(customPattern).test(url)
    return /toasttab\.com\/.*\/confirm/.test(url) ||
           /toasttab\.com\/.*\/order-confirmation/.test(url)
  },
}

// ─── Square Adapter ─────────────────────────────────────────────────────────

const squareAdapter: POSAdapter = {
  buildOrderingURL(orderingUrl, sessionId, _userPhone, discountCode) {
    const sep = orderingUrl.includes('?') ? '&' : '?'
    let url = `${orderingUrl}${sep}${UTM_PARAMS}&session_id=${sessionId}`
    if (discountCode) url += `&discount=${discountCode}`
    return url
  },

  getPhoneInjectJS(phoneNumber, customSelector) {
    return buildInjectJS(customSelector || 'input[name="phone"], input[type="tel"]', phoneNumber)
  },

  getDiscountInjectJS(discountCode, customSelector) {
    return buildInjectJS(
      customSelector || 'input[name="discount"], input[placeholder*="discount" i]',
      discountCode
    )
  },

  detectOrderConfirmation(url, customPattern) {
    if (customPattern) return new RegExp(customPattern).test(url)
    return /square\.site\/.*\/confirmation/.test(url) ||
           /squareup\.com\/.*\/receipt/.test(url)
  },
}

// ─── Shopify Adapter ────────────────────────────────────────────────────────

const shopifyAdapter: POSAdapter = {
  buildOrderingURL(orderingUrl, sessionId, _userPhone, discountCode) {
    let url = orderingUrl
    if (discountCode) {
      url = `${url.replace(/\/$/, '')}/discount/${discountCode}`
    }
    const sep = url.includes('?') ? '&' : '?'
    return `${url}${sep}${UTM_PARAMS}&session_id=${sessionId}`
  },

  getPhoneInjectJS(phoneNumber, customSelector) {
    return buildInjectJS(
      customSelector || '#checkout_shipping_address_phone, input[autocomplete="tel"]',
      phoneNumber
    )
  },

  getDiscountInjectJS(discountCode, customSelector) {
    return buildInjectJS(
      customSelector || 'input[name="checkout[reduction_code]"], input[placeholder*="discount" i]',
      discountCode
    )
  },

  detectOrderConfirmation(url, customPattern) {
    if (customPattern) return new RegExp(customPattern).test(url)
    return /\/thank_you/.test(url) || /\/orders\/.*\/confirm/.test(url)
  },
}

// ─── Other (Fallback) Adapter ───────────────────────────────────────────────

const otherAdapter: POSAdapter = {
  buildOrderingURL(orderingUrl, sessionId) {
    const sep = orderingUrl.includes('?') ? '&' : '?'
    return `${orderingUrl}${sep}${UTM_PARAMS}&session_id=${sessionId}`
  },

  getPhoneInjectJS(phoneNumber, customSelector) {
    if (customSelector) return buildInjectJS(customSelector, phoneNumber)
    return '' // No injection for unknown POS
  },

  getDiscountInjectJS(discountCode, customSelector) {
    if (customSelector) return buildInjectJS(customSelector, discountCode)
    return '' // No injection for unknown POS
  },

  detectOrderConfirmation(url, customPattern) {
    if (customPattern) return new RegExp(customPattern).test(url)
    return false // Manual confirmation via "I completed my order" button
  },
}

// ─── Factory ────────────────────────────────────────────────────────────────

/**
 * Factory for creating POS adapters by platform type.
 *
 * EXTENSIBILITY: To add a new POS (WooCommerce, Clover, SpotOn):
 *   1. Create a new adapter object implementing the POSAdapter interface
 *   2. Add the pos_type to the POSType union
 *   3. Register it in the adapters map below
 * No changes needed in WebView screen, merchant card, attribution, or cluster layer.
 */
const adapters: Record<string, POSAdapter> = {
  toast: toastAdapter,
  square: squareAdapter,
  shopify: shopifyAdapter,
  other: otherAdapter,
}

export function getAdapter(posType: string | null | undefined): POSAdapter {
  return adapters[posType || 'other'] || otherAdapter
}
