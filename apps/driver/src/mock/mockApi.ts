// Mock API functions that return fixtures with simulated delays
import type {
  MockCaptureIntentRequest,
  CaptureIntentResponse,
  MerchantDetailsResponse,
  WalletActivateResponse,
  ChargerWithExperiences,
} from './types'
import {
  MOCK_SESSION_ID,
  MOCK_MERCHANTS,
  MOCK_CHARGERS,
  getMerchantDetailsFixture,
  createWalletActivationResponse,
} from './fixtures'

// Simulate network delay (50-150ms for realistic feel)
function delay(ms: number = 100): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Mock capture intent - returns merchants for charging state, chargers for pre-charging state
 */
export async function captureIntentMock(
  request: MockCaptureIntentRequest
): Promise<CaptureIntentResponse> {
  await delay(80)

  const state = request.state || 'charging'

  if (state === 'pre-charging') {
    // Return chargers for pre-charging state
    return {
      session_id: MOCK_SESSION_ID,
      confidence_tier: 'A',
      charger_summary: {
        id: MOCK_CHARGERS[0].id,
        name: MOCK_CHARGERS[0].name,
        distance_m: MOCK_CHARGERS[0].distance_m,
        network_name: MOCK_CHARGERS[0].network_name,
      },
      merchants: [], // Empty merchants array for pre-charging
      next_actions: {
        request_wallet_pass: false,
        require_vehicle_onboarding: false,
      },
    }
  }

  // Return merchants for charging state
  return {
    session_id: MOCK_SESSION_ID,
    confidence_tier: 'A',
    merchants: MOCK_MERCHANTS,
    next_actions: {
      request_wallet_pass: true,
      require_vehicle_onboarding: false,
    },
  }
}

/**
 * Mock merchant details
 */
export async function getMerchantDetailsMock(
  merchantId: string,
  _sessionId?: string
): Promise<MerchantDetailsResponse> {
  await delay(60)
  return getMerchantDetailsFixture(merchantId)
}

/**
 * Mock charger details with nearby experiences
 */
export async function getChargerDetailsMock(
  chargerId: string
): Promise<{ charger: ChargerWithExperiences }> {
  await delay(60)
  const charger = MOCK_CHARGERS.find((c) => c.id === chargerId) || MOCK_CHARGERS[0]
  return { charger }
}

/**
 * Mock wallet activation
 */
export async function activateExclusiveMock(
  merchantId: string,
  _sessionId: string
): Promise<WalletActivateResponse> {
  await delay(120) // Slightly longer for activation
  return createWalletActivationResponse(merchantId)
}

/**
 * Get all mock chargers (for pre-charging screen)
 */
export function getAllMockChargers(): ChargerWithExperiences[] {
  return MOCK_CHARGERS
}

/**
 * Get all mock merchants (for charging screen)
 */
export function getAllMockMerchants(): typeof MOCK_MERCHANTS {
  return MOCK_MERCHANTS
}

