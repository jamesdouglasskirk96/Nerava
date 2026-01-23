# Secrets Manager Integration Guide

This document describes how to enable AWS Secrets Manager for secret storage in the Nerava platform.

## Overview

The Nerava platform uses a secrets provider abstraction (`app/core/secrets.py`) that supports:
- **Environment Variables** (default) - Secrets stored in environment variables
- **AWS Secrets Manager** (optional) - Secrets stored in AWS Secrets Manager

By default, the application reads secrets from environment variables. AWS Secrets Manager can be enabled by setting the `SECRETS_PROVIDER` environment variable.

## Current Implementation (Environment Variables)

Secrets are currently read from environment variables using the `EnvSecretProvider`:

```python
from app.core.secrets import get_secret

database_url = get_secret("DATABASE_URL")
jwt_secret = get_secret("JWT_SECRET")
```

## Enabling AWS Secrets Manager

### Prerequisites

1. **Install boto3**:
   ```bash
   pip install boto3
   ```

2. **AWS Credentials**: Configure AWS credentials using one of:
   - AWS IAM role (recommended for EC2/ECS/Lambda)
   - AWS credentials file (`~/.aws/credentials`)
   - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)

3. **IAM Permissions**: Ensure the IAM role/user has permissions to read secrets:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "secretsmanager:GetSecretValue",
           "secretsmanager:DescribeSecret"
         ],
         "Resource": "arn:aws:secretsmanager:*:*:secret:nerava/*"
       }
     ]
   }
   ```

### Configuration

Set the following environment variables:

```bash
# Enable AWS Secrets Manager
export SECRETS_PROVIDER=aws

# Optional: AWS region (defaults to us-east-1)
export AWS_DEFAULT_REGION=us-east-1
```

### Storing Secrets in AWS Secrets Manager

Create secrets in AWS Secrets Manager:

```bash
# Create a secret
aws secretsmanager create-secret \
  --name nerava/DATABASE_URL \
  --secret-string "postgresql://user:pass@host:5432/dbname"

# Create another secret
aws secretsmanager create-secret \
  --name nerava/JWT_SECRET \
  --secret-string "your-jwt-secret-here"
```

### Using Secrets

The application will automatically read from AWS Secrets Manager when `SECRETS_PROVIDER=aws`:

```python
from app.core.secrets import get_secret

# Reads from AWS Secrets Manager if SECRETS_PROVIDER=aws
database_url = get_secret("nerava/DATABASE_URL")
jwt_secret = get_secret("nerava/JWT_SECRET")
```

## Migration Path

### Step 1: Create Secrets in AWS Secrets Manager

Create all required secrets in AWS Secrets Manager using the naming convention `nerava/SECRET_NAME`:

```bash
# List of secrets to migrate
SECRETS=(
  "DATABASE_URL"
  "JWT_SECRET"
  "REDIS_URL"
  "TOKEN_ENCRYPTION_KEY"
  "STRIPE_SECRET"
  "SQUARE_WEBHOOK_SIGNATURE_KEY"
  # ... etc
)

for secret in "${SECRETS[@]}"; do
  aws secretsmanager create-secret \
    --name "nerava/$secret" \
    --secret-string "$(printenv $secret)"
done
```

### Step 2: Update Application Configuration

Set `SECRETS_PROVIDER=aws` in your deployment environment:

```bash
# In your deployment config (e.g., ECS task definition, Kubernetes secret)
export SECRETS_PROVIDER=aws
export AWS_DEFAULT_REGION=us-east-1
```

### Step 3: Update Secret Names

Update code to use AWS secret names (if using custom names):

```python
# Old (env vars)
db_url = get_secret("DATABASE_URL")

# New (AWS Secrets Manager)
db_url = get_secret("nerava/DATABASE_URL")
```

### Step 4: Test

Verify secrets are being read from AWS Secrets Manager:

```bash
# Check logs for: "Using AWS Secrets Manager provider"
# Verify application starts successfully
```

## Fallback Behavior

If AWS Secrets Manager is enabled but a secret is not found, the provider will return `None`. The application should handle this gracefully (e.g., fail-fast on startup if required secrets are missing).

## Security Considerations

1. **Least Privilege**: Grant only the minimum IAM permissions needed
2. **Secret Rotation**: Use AWS Secrets Manager rotation to rotate secrets automatically
3. **Encryption**: Secrets are encrypted at rest in AWS Secrets Manager
4. **Audit**: Enable CloudTrail to audit secret access

## Troubleshooting

### Secret Not Found

If a secret is not found in AWS Secrets Manager:
- Check the secret name matches exactly (case-sensitive)
- Verify IAM permissions allow `secretsmanager:GetSecretValue`
- Check AWS region matches `AWS_DEFAULT_REGION`

### boto3 Import Error

If you see `ImportError: boto3 is required`:
```bash
pip install boto3
```

### Fallback to Environment Variables

If AWS Secrets Manager fails, the application will not automatically fall back to environment variables. Ensure AWS credentials and permissions are correctly configured.

## Code Example

```python
from app.core.secrets import get_secret, get_secret_provider

# Get secret using configured provider
database_url = get_secret("DATABASE_URL")

# Check which provider is being used
provider = get_secret_provider()
if isinstance(provider, AWSSecretsManagerProvider):
    print("Using AWS Secrets Manager")
else:
    print("Using environment variables")
```







