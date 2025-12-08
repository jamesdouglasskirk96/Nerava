/**
 * Charging State Service
 * 
 * Centralized logic for determining charging state and optimal charging times.
 * Used by both Wallet hero and Discovery charge guidance capsule.
 */

/**
 * Get current charging state and next change time
 * @returns {Object} { state: 'off-peak'|'peak'|'idle', nextChangeTime: Date, countdown: string }
 */
export function getChargingState() {
  const now = new Date();
  const hour = now.getHours();
  
  // Simplified logic: Off-peak is typically 10 PM - 6 AM, Peak is 6 AM - 10 PM
  // This can be enhanced with actual utility rate schedules later
  let state = 'peak';
  let nextChangeHour = 22; // 10 PM
  
  if (hour >= 22 || hour < 6) {
    state = 'off-peak';
    nextChangeHour = hour < 6 ? 6 : 22;
  } else {
    state = 'peak';
    nextChangeHour = 22;
  }
  
  // Calculate next change time
  const nextChange = new Date(now);
  nextChange.setHours(nextChangeHour, 0, 0, 0);
  
  // If next change is earlier today, it's tomorrow
  if (nextChange <= now) {
    nextChange.setDate(nextChange.getDate() + 1);
  }
  
  // Calculate countdown
  const diffMs = nextChange - now;
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  
  let countdown = '';
  if (diffHours > 0) {
    countdown = `${diffHours}h ${diffMinutes}m`;
  } else {
    countdown = `${diffMinutes}m`;
  }
  
  return {
    state,
    nextChangeTime: nextChange,
    countdown,
    nextChangeHour
  };
}

/**
 * Get optimal charging time window
 * @returns {Object} { startTime: Date, endTime: Date, message: string }
 */
export function getOptimalChargingTime() {
  const { state, nextChangeTime, countdown } = getChargingState();
  const now = new Date();
  
  if (state === 'off-peak') {
    return {
      startTime: now,
      endTime: nextChangeTime,
      message: `Best time to charge: Now (Off-peak ends in ${countdown})`,
      isOptimal: true
    };
  } else {
    // Next off-peak window
    const nextOffPeak = new Date(nextChangeTime);
    return {
      startTime: nextOffPeak,
      endTime: new Date(nextOffPeak.getTime() + 8 * 60 * 60 * 1000), // 8 hour window
      message: `Best time to charge: ${formatTime(nextChangeTime)} (Off-peak starts in ${countdown})`,
      isOptimal: false
    };
  }
}

/**
 * Format time for display (e.g., "6:40 PM")
 */
function formatTime(date) {
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;
  const displayMinutes = minutes.toString().padStart(2, '0');
  return `${displayHours}:${displayMinutes} ${ampm}`;
}

/**
 * Get charging state display info for UI
 * @returns {Object} { label: string, color: string, icon: string }
 */
export function getChargingStateDisplay() {
  const { state } = getChargingState();
  
  const displays = {
    'off-peak': {
      label: 'Off-peak',
      color: '#22c55e', // green
      icon: '🌙',
      description: 'Best time to charge'
    },
    'peak': {
      label: 'Peak',
      color: '#f59e0b', // amber
      icon: '⚡',
      description: 'Higher rates'
    },
    'idle': {
      label: 'Idle',
      color: '#6b7280', // gray
      icon: '💤',
      description: 'Not charging'
    }
  };
  
  return displays[state] || displays.idle;
}

