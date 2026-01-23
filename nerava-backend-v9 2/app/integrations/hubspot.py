"""HubSpot CRM integration for merchant leads."""
import logging
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class HubSpotClient:
    """Client for HubSpot CRM API."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self):
        self.token = settings.HUBSPOT_PRIVATE_APP_TOKEN
        self.enabled = settings.HUBSPOT_ENABLED and settings.HUBSPOT_SEND_LIVE

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def upsert_contact(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        business_name: Optional[str] = None,
        website: Optional[str] = None,
        address: Optional[str] = None,
        source: str = "nerava",
    ) -> Optional[str]:
        """
        Create or update a HubSpot contact. Returns contact ID or None on failure.
        Idempotent: uses email as unique key.
        """
        if not self.enabled:
            logger.debug("[HubSpot] Disabled, skipping contact upsert")
            return None

        if not email and not phone:
            logger.warning("[HubSpot] Cannot upsert contact without email or phone")
            return None

        properties = {"hs_lead_status": "NEW", "source": source}
        if email:
            properties["email"] = email
        if phone:
            properties["phone"] = phone
        if business_name:
            properties["company"] = business_name
        if website:
            properties["website"] = website
        if address:
            properties["address"] = address

        try:
            async with httpx.AsyncClient() as client:
                # Try to find existing contact by email
                if email:
                    search_response = await client.post(
                        f"{self.BASE_URL}/crm/v3/objects/contacts/search",
                        headers=self.headers,
                        json={
                            "filterGroups": [{
                                "filters": [{
                                    "propertyName": "email",
                                    "operator": "EQ",
                                    "value": email
                                }]
                            }]
                        },
                        timeout=30.0,
                    )

                    if search_response.status_code == 200:
                        results = search_response.json().get("results", [])
                        if results:
                            # Update existing contact
                            contact_id = results[0]["id"]
                            update_response = await client.patch(
                                f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}",
                                headers=self.headers,
                                json={"properties": properties},
                                timeout=30.0,
                            )
                            if update_response.status_code == 200:
                                logger.info(f"[HubSpot] Updated contact {contact_id}")
                                return contact_id

                # Create new contact
                create_response = await client.post(
                    f"{self.BASE_URL}/crm/v3/objects/contacts",
                    headers=self.headers,
                    json={"properties": properties},
                    timeout=30.0,
                )

                if create_response.status_code == 201:
                    contact_id = create_response.json().get("id")
                    logger.info(f"[HubSpot] Created contact {contact_id}")
                    return contact_id
                else:
                    logger.warning(f"[HubSpot] Failed to create contact: {create_response.status_code}")
                    return None

        except Exception as e:
            logger.exception(f"[HubSpot] Error upserting contact: {e}")
            from app.core.sentry import capture_exception
            capture_exception(e, extra={"email_domain": email.split("@")[-1] if email else None})
            return None  # Fail open - don't block the request


# Singleton instance
_hubspot_client: Optional[HubSpotClient] = None


def get_hubspot_client() -> HubSpotClient:
    """Get the HubSpot client singleton."""
    global _hubspot_client
    if _hubspot_client is None:
        _hubspot_client = HubSpotClient()
    return _hubspot_client


