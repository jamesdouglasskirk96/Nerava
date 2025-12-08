/**
 * Branded Charger Pins for Map
 * 
 * Creates network-branded charger pins similar to AmpUp/PlugShare
 * with status colors and zoom-based scaling
 */

/* globals L */

// Network logo mapping (using local placeholder to avoid 403s from third-party domains)
const MERCHANT_LOGO_PLACEHOLDER = './img/avatar-default.png';
const NETWORK_LOGOS = {
  'tesla': MERCHANT_LOGO_PLACEHOLDER,
  'chargepoint': MERCHANT_LOGO_PLACEHOLDER,
  'evgo': MERCHANT_LOGO_PLACEHOLDER,
  'electrify_america': MERCHANT_LOGO_PLACEHOLDER,
  'volta': MERCHANT_LOGO_PLACEHOLDER,
  'blink': MERCHANT_LOGO_PLACEHOLDER,
  'flo': MERCHANT_LOGO_PLACEHOLDER,
  'ampup': MERCHANT_LOGO_PLACEHOLDER,
  'generic': 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzIDJMMyAxNGg3bC0xIDggMTAtMTJoLTdsMS04eiIgZmlsbD0iIzJGNkJGRiIvPgo8L3N2Zz4K' // Generic lightning bolt
};

// Status colors
const STATUS_COLORS = {
  'available': '#34C759',   // Green
  'in_use': '#FF9500',      // Orange
  'broken': '#FF3B30',      // Red
  'unknown': '#C7C7CC'      // Grey
};

/**
 * Get network logo URL
 */
function getNetworkLogo(network) {
  if (!network) return NETWORK_LOGOS.generic;
  
  const networkKey = network.toLowerCase()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_]/g, '');
  
  return NETWORK_LOGOS[networkKey] || NETWORK_LOGOS.generic;
}

/**
 * Get status color
 */
function getStatusColor(status = 'unknown') {
  return STATUS_COLORS[status] || STATUS_COLORS.unknown;
}

/**
 * Create branded charger pin HTML
 */
function createPinHTML(network, status, scale = 1.0) {
  const logoUrl = getNetworkLogo(network);
  const statusColor = getStatusColor(status);
  const size = Math.round(48 * scale);
  const logoSize = Math.round(28 * scale);
  const borderWidth = Math.max(2, Math.round(3 * scale));
  const tailSize = Math.round(6 * scale);
  const tailHeight = Math.round(8 * scale);
  
  // Escape quotes for inline styles
  const escapedLogoUrl = logoUrl.replace(/'/g, "\\'");
  const escapedGeneric = NETWORK_LOGOS.generic.replace(/'/g, "\\'");
  
  return `
    <div class="charger-pin" data-scale="${scale}" style="
      width: ${size}px;
      height: ${size + tailHeight}px;
      position: relative;
      --pin-scale: ${scale};
      transform: scale(${scale});
      transition: transform 0.2s ease, filter 0.2s ease;
    ">
      <div class="charger-pin-circle" style="
        width: ${size}px;
        height: ${size}px;
        background: ${statusColor};
        border: ${borderWidth}px solid #FFFFFF;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
        margin: 0 auto;
      ">
        <img 
          src="${escapedLogoUrl}" 
          alt="${(network || 'Charger').replace(/"/g, '&quot;')}"
          style="
            width: ${logoSize}px;
            height: ${logoSize}px;
            object-fit: contain;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
          "
          onerror="this.onerror=null; this.src='${escapedGeneric}';"
        />
      </div>
      <div class="charger-pin-tail" style="
        width: 0;
        height: 0;
        border-left: ${tailSize}px solid transparent;
        border-right: ${tailSize}px solid transparent;
        border-top: ${tailHeight}px solid ${statusColor};
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
      "></div>
    </div>
  `;
}

/**
 * Create Leaflet icon for branded charger pin
 */
export function createChargerPinIcon(network, status = 'unknown', zoom = 15) {
  // Calculate scale based on zoom
  let scale = 1.0;
  if (zoom < 12) {
    scale = 0.6;
  } else if (zoom >= 12 && zoom <= 14) {
    scale = 0.8;
  } else {
    scale = 1.0;
  }
  
  const html = createPinHTML(network, status, scale);
  const iconSize = Math.round(48 * scale);
  const tailHeight = Math.round(8 * scale);
  const totalHeight = iconSize + tailHeight;
  
  const icon = L.divIcon({
    html: html,
    className: 'charger-pin-marker',
    iconSize: [iconSize, totalHeight],
    iconAnchor: [iconSize / 2, totalHeight], // Anchor at bottom of tail
    popupAnchor: [0, -totalHeight - 5]
  });
  
  // Store network and status in icon for later updates
  icon._network = network;
  icon._status = status;
  
  return icon;
}

/**
 * Update pin scale based on zoom level
 */
export function updatePinScale(marker, zoom) {
  const icon = marker.options.icon;
  if (!icon || !icon._network) return;
  
  const network = icon._network;
  const status = icon._status || 'available';
  const newIcon = createChargerPinIcon(network, status, zoom);
  marker.setIcon(newIcon);
}

/**
 * Animate pin on tap/click
 */
export function animatePinTap(marker) {
  const pinElement = marker.getElement();
  if (!pinElement) return;
  
  const pin = pinElement.querySelector('.charger-pin');
  if (!pin) return;
  
  // Get current scale from data attribute or default to 1
  const currentScale = parseFloat(pin.dataset.scale || '1.0');
  
  // Animate to 1.1x of current scale
  pin.style.transition = 'transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)';
  pin.style.transform = `scale(${currentScale * 1.1})`;
  
  // Increase shadow
  const circle = pinElement.querySelector('.charger-pin-circle');
  if (circle) {
    circle.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.25)';
    circle.style.transition = 'box-shadow 0.2s ease';
  }
  
  // Reset after animation
  setTimeout(() => {
    pin.style.transition = 'transform 0.2s ease, filter 0.2s ease';
    pin.style.transform = `scale(${currentScale})`;
    if (circle) {
      circle.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
    }
  }, 200);
}

