import os
from typing import Dict, Any
import uuid
import json

class MockSquareClient:
    """Mock Square client for development when API keys are not provided"""
    
    def __init__(self):
        self.environment = os.getenv('SQUARE_ENV', 'sandbox')
        self.access_token = os.getenv('SQUARE_ACCESS_TOKEN', 'REPLACE_ME')
        self.is_mock = self.access_token == 'REPLACE_ME'
        
    class CheckoutApi:
        def __init__(self, client):
            self.client = client
            
        async def create_payment_link(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
            if self.client.is_mock:
                # Mock response for development
                payment_id = str(uuid.uuid4())
                mock_url = f"http://127.0.0.1:8001/mock-checkout.html?payment_id={payment_id}"
                
                return {
                    'result': {
                        'paymentLink': {
                            'url': mock_url,
                            'id': payment_id
                        }
                    }
                }
            else:
                # Real Square API call would go here
                # For now, return mock response
                payment_id = str(uuid.uuid4())
                mock_url = f"http://127.0.0.1:8001/mock-checkout.html?payment_id={payment_id}"
                
                return {
                    'result': {
                        'paymentLink': {
                            'url': mock_url,
                            'id': payment_id
                        }
                    }
                }
    
    def __init__(self):
        self.environment = os.getenv('SQUARE_ENV', 'sandbox')
        self.access_token = os.getenv('SQUARE_ACCESS_TOKEN', 'REPLACE_ME')
        self.is_mock = self.access_token == 'REPLACE_ME'
        self.checkoutApi = self.CheckoutApi(self)

# Create global instance
square = MockSquareClient()
