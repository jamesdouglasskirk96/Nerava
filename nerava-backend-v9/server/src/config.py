import os

class Config:
    SQUARE_ENV = os.getenv('SQUARE_ENV', 'sandbox')
    SQUARE_ACCESS_TOKEN = os.getenv('SQUARE_ACCESS_TOKEN', 'REPLACE_ME')
    SQUARE_LOCATION_ID = os.getenv('SQUARE_LOCATION_ID', 'REPLACE_ME')
    SQUARE_WEBHOOK_SIGNATURE_KEY = os.getenv('SQUARE_WEBHOOK_SIGNATURE_KEY', 'dev-signature')
    SQUARE_APPLICATION_ID = os.getenv('SQUARE_APPLICATION_ID', 'REPLACE_ME')
    PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', 'http://127.0.0.1:8001')
    DEV_WEBHOOK_BYPASS = os.getenv('DEV_WEBHOOK_BYPASS', 'true').lower() == 'true'
    DEMO_USER_ID = os.getenv('DEMO_USER_ID', 'user-demo-1')
    
    # Dual-event verification config
    VERIFICATION_WINDOW_MIN = int(os.getenv('VERIFICATION_WINDOW_MIN', '120'))
    TELEMETRY_LAG_MIN = int(os.getenv('TELEMETRY_LAG_MIN', '10'))
    R1_CHARGER_M = int(os.getenv('R1_CHARGER_M', '40'))
    R2_MERCHANT_M = int(os.getenv('R2_MERCHANT_M', '100'))
    MIN_KWH = float(os.getenv('MIN_KWH', '2.0'))
    ALLOW_MERCHANT_DWELL_FALLBACK = os.getenv('ALLOW_MERCHANT_DWELL_FALLBACK', 'true').lower() == 'true'
    DAILY_REWARD_CAP_CENTS = int(os.getenv('DAILY_REWARD_CAP_CENTS', '1500'))

config = Config()
