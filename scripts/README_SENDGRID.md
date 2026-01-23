# SendGrid Email Configuration

This document describes how to configure SendGrid email service for the Nerava backend.

## Configuration

### Environment Variables

The backend uses the following environment variables for SendGrid:

- `SENDGRID_API_KEY` - Your SendGrid API key (required)
- `EMAIL_PROVIDER` - Email provider name (set to `sendgrid` to enable SendGrid)
- `EMAIL_FROM` - From email address (defaults to `noreply@nerava.network`)

### Current SendGrid API Key

```
SG.YOUR_SENDGRID_API_KEY_HERE
```

## Updating App Runner Service

To update the App Runner service with SendGrid API key:

```bash
export SENDGRID_API_KEY="SG.YOUR_SENDGRID_API_KEY_HERE"
export EMAIL_PROVIDER="sendgrid"
export EMAIL_FROM="noreply@nerava.network"
export SERVICE_NAME="nerava-backend"

./scripts/update_sendgrid.sh
```

Or use the deployment script which now includes SendGrid configuration:

```bash
export SENDGRID_API_KEY="SG.YOUR_SENDGRID_API_KEY_HERE"
export EMAIL_PROVIDER="sendgrid"
export EMAIL_FROM="noreply@nerava.network"

./scripts/deploy_api_apprunner.sh
```

## Email Sender Factory

The backend uses an email sender factory that automatically selects the appropriate sender based on configuration:

- If `EMAIL_PROVIDER=sendgrid` and `SENDGRID_API_KEY` is set → Uses `SendGridEmailSender`
- Otherwise → Uses `ConsoleEmailSender` (logs emails to console)

## Testing SendGrid

### 1. Check Configuration

Verify that SendGrid is configured correctly:

```bash
curl https://api.nerava.network/v1/health
```

Check the logs to see if SendGrid is initialized.

### 2. Send Test Email

You can test email sending through any endpoint that sends emails (e.g., magic link, password reset, etc.).

### 3. Check SendGrid Dashboard

Monitor email delivery in the SendGrid dashboard:
- https://app.sendgrid.com/activity

## DNS Configuration

SendGrid requires DNS records to be configured for domain authentication. These should already be set up:

- **SPF Record**: `v=spf1 include:_spf.google.com include:sendgrid.net ~all`
- **DKIM Records**: CNAME records for `s1._domainkey` and `s2._domainkey`
- **DMARC Record**: TXT record for `_dmarc.nerava.network`

Verify domain authentication in SendGrid dashboard:
- https://app.sendgrid.com/settings/sender_auth

## Configuration Files

- Email sender factory: `nerava-backend-v9 2/app/services/email/factory.py`
- SendGrid implementation: `nerava-backend-v9 2/app/services/email/sendgrid.py`
- Backend config: `nerava-backend-v9 2/app/core/config.py`

## Features

- **Production Email Delivery**: Real email sending via SendGrid API
- **Error Handling**: Failed emails are logged and sent to Sentry
- **Reply-To Support**: Configurable reply-to address
- **HTML and Plain Text**: Supports both HTML and plain text email content
- **Timeout Protection**: 30-second timeout for API calls

## Troubleshooting

### Emails Not Sending

1. Check that `EMAIL_PROVIDER=sendgrid` is set
2. Verify `SENDGRID_API_KEY` is correct
3. Check SendGrid dashboard for API errors
4. Verify domain authentication is complete
5. Check CloudWatch logs for error messages

### Domain Authentication Issues

1. Verify DNS records are correct:
   ```bash
   dig TXT nerava.network | grep spf
   dig CNAME s1._domainkey.nerava.network
   dig CNAME s2._domainkey.nerava.network
   ```

2. Check SendGrid dashboard for authentication status

3. Wait for DNS propagation (can take up to 48 hours)

## SendGrid Dashboard

Access your SendGrid dashboard at:
https://app.sendgrid.com/

Key sections:
- **Activity**: View sent emails and delivery status
- **Settings > Sender Authentication**: Verify domain authentication
- **Settings > API Keys**: Manage API keys


