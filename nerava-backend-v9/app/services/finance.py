from typing import Dict, Any

def offers(user_id: str) -> Dict[str, Any]:
    """
    Get ESG finance gateway offers.
    
    TODO: Implement real finance offers logic
    - Check user eligibility
    - Query partner offers
    - Calculate APR benefits
    - Target p95 < 250ms with caching
    """
    
    # Stub implementation
    return {
        "offers": [
            {
                "partner": "Green Bank",
                "apr_delta_bps": -50,
                "terms_url": "https://greenbank.com/nerava-offer",
                "eligibility": {"min_score": 600}
            },
            {
                "partner": "Eco Credit Union",
                "apr_delta_bps": -75,
                "terms_url": "https://ecocu.org/nerava-special",
                "eligibility": {"min_score": 700}
            },
            {
                "partner": "Sustainable Finance Co",
                "apr_delta_bps": -100,
                "terms_url": "https://sustainable.finance/nerava-premium",
                "eligibility": {"min_score": 800}
            }
        ]
    }
