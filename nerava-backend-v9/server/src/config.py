import os

class Config:
    SQUARE_ENV = os.getenv('SQUARE_ENV', 'sandbox')
    SQUARE_ACCESS_TOKEN = os.getenv('SQUARE_ACCESS_TOKEN', 'REPLACE_ME')
    SQUARE_LOCATION_ID = os.getenv('SQUARE_LOCATION_ID', 'REPLACE_ME')
    SQUARE_WEBHOOK_SIGNATURE_KEY = os.getenv('SQUARE_WEBHOOK_SIGNATURE_KEY', 'REPLACE_ME')
    SQUARE_APPLICATION_ID = os.getenv('SQUARE_APPLICATION_ID', 'REPLACE_ME')
    PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', 'http://127.0.0.1:8001')
    DEV_WEBHOOK_BYPASS = os.getenv('DEV_WEBHOOK_BYPASS', 'true').lower() == 'true'
    DEMO_USER_ID = os.getenv('DEMO_USER_ID', 'user-demo-1')

config = Config()
