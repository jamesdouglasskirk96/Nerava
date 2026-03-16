"""
SES Email Sender — sends transactional email via Amazon SES (boto3).
"""

import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from .email_sender import EmailSender

logger = logging.getLogger(__name__)


class SESEmailSender(EmailSender):
    """Send email via Amazon SES using boto3."""

    def __init__(self, region: str = "us-east-1", sender: str = "noreply@nerava.network"):
        self._client = boto3.client("ses", region_name=region)
        self._sender = sender

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        body: dict = {"Text": {"Charset": "UTF-8", "Data": body_text}}
        if body_html:
            body["Html"] = {"Charset": "UTF-8", "Data": body_html}

        try:
            self._client.send_email(
                Source=self._sender,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Charset": "UTF-8", "Data": subject},
                    "Body": body,
                },
            )
            logger.info("SES email sent to %s subject=%s", to_email, subject)
            return True
        except ClientError as exc:
            logger.error("SES send_email failed: %s", exc)
            return False
