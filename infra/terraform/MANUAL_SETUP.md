# Manual Setup Instructions for AWS Deployment

This document outlines the manual steps required before running Terraform to deploy Nerava to AWS.

## Prerequisites

1. AWS Account with appropriate permissions
2. Domain `nerava.network` registered (or access to manage DNS)
3. GitHub repository access (for CI/CD)

## Step 1: Route53 Domain Setup

### Option A: Domain Already in Route53

If `nerava.network` is already registered in Route53:

1. Go to Route53 Console → Hosted Zones
2. Find the hosted zone for `nerava.network`
3. Copy the Hosted Zone ID (e.g., `Z1234567890ABC`)
4. Set `route53_zone_id` in `terraform.tfvars` to this value

### Option B: Domain Registered Elsewhere

If `nerava.network` is registered with another registrar:

1. Go to Route53 Console → Hosted Zones → Create Hosted Zone
2. Domain name: `nerava.network`
3. Type: Public hosted zone
4. Create the hosted zone
5. Copy the 4 nameservers from the NS record
6. Go to your domain registrar and update nameservers to these 4 values
7. Wait for DNS propagation (can take up to 48 hours, usually < 1 hour)
8. Copy the Hosted Zone ID and set `route53_zone_id` in `terraform.tfvars` (or leave empty to let Terraform create it)

## Step 2: ACM Certificate

1. Go to AWS Certificate Manager (ACM) Console
2. Request a public certificate
3. Domain names:
   - `*.nerava.network` (wildcard for all subdomains)
   - `nerava.network` (apex domain)
4. Validation method: DNS validation (recommended) or Email validation
5. If using DNS validation:
   - ACM will provide CNAME records to add to Route53
   - Go to Route53 → Hosted Zones → `nerava.network`
   - Create the CNAME records as specified by ACM
   - Wait for validation (usually 5-30 minutes)
6. Copy the Certificate ARN (e.g., `arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012`)
7. Set `acm_certificate_arn` in `terraform.tfvars` to this value

**Important:** Certificate must be in the same region as your ALB (us-east-1 by default).

## Step 3: GitHub OIDC Setup (Recommended)

### Create OIDC Provider

1. Go to IAM Console → Identity providers → Add provider
2. Provider type: OpenID Connect
3. Provider URL: `https://token.actions.githubusercontent.com`
4. Audience: `sts.amazonaws.com`
5. Click "Add provider"
6. Copy the Provider ARN (e.g., `arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com`)
7. Set `github_oidc_provider_arn` in `terraform.tfvars` to this value

### Create GitHub Actions IAM Role

Terraform will create this role automatically if `github_repository` and `github_oidc_provider_arn` are set.

Alternatively, create manually:

1. Go to IAM Console → Roles → Create role
2. Trusted entity type: Web identity
3. Identity provider: Select the GitHub OIDC provider created above
4. Audience: `sts.amazonaws.com`
5. Conditions:
   - Key: `token.actions.githubusercontent.com:sub`
   - Value: `repo:your-org/nerava:*` (replace with your GitHub repo)
6. Attach policies:
   - `AmazonEC2FullAccess` (or more restrictive)
   - `AmazonECS_FullAccess` (or more restrictive)
   - `AmazonRDSFullAccess` (or more restrictive)
   - `SecretsManagerReadWrite` (or more restrictive)
   - `AmazonEC2ContainerRegistryFullAccess` (or more restrictive)
7. Name: `nerava-github-actions-role`
8. Create role
9. Copy the Role ARN

### Configure GitHub Repository

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add secret: `AWS_ROLE_ARN` = Role ARN from above
3. Add secret: `AWS_REGION` = `us-east-1` (or your region)

**Note:** If not using OIDC, you'll need to add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets instead.

## Step 4: Secrets Manager Setup

Terraform will create the secret structures, but you need to populate them with actual values.

### After First Terraform Apply

After running `terraform apply` for the first time, update secrets with real values:

1. Go to AWS Secrets Manager Console
2. For each secret, click "Retrieve secret value" → "Edit"
3. Update with real values:

#### `nerava/backend/database`
- This will be auto-populated with the RDS connection string after RDS is created
- No manual update needed if using Terraform-managed RDS

#### `nerava/backend/jwt-secret`
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```
Copy the output and paste into the secret.

#### `nerava/backend/token-encryption-key`
```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```
Copy the output and paste into the secret.

#### `nerava/backend/twilio`
```json
{
  "account_sid": "your_twilio_account_sid",
  "auth_token": "your_twilio_auth_token",
  "verify_service_sid": "your_twilio_verify_service_sid",
  "from_number": ""  // Optional, only if using twilio_sms
}
```

#### `nerava/backend/google`
```json
{
  "client_id": "your_google_client_id",
  "oauth_client_id": "your_google_oauth_client_id",
  "oauth_client_secret": "your_google_oauth_client_secret",
  "redirect_uri": "https://api.nerava.network/v1/merchants/google/callback",
  "places_api_key": "your_google_places_api_key"
}
```

#### `nerava/backend/square`
```json
{
  "env": "production",
  "application_id": "your_square_app_id",
  "application_secret": "your_square_app_secret",
  "redirect_url": "https://api.nerava.network/v1/merchants/square/callback",
  "webhook_signature_key": "your_square_webhook_signature_key"
}
```

#### `nerava/backend/stripe`
```json
{
  "secret_key": "sk_live_your_live_secret_key",
  "webhook_secret": "whsec_your_webhook_secret",
  "connect_client_id": "ca_your_connect_client_id"
}
```

#### `nerava/backend/smartcar`
```json
{
  "client_id": "your_smartcar_client_id",
  "client_secret": "your_smartcar_client_secret",
  "redirect_uri": "https://api.nerava.network/oauth/smartcar/callback",
  "mode": "live",
  "state_secret": "generate_with_openssl_rand_hex_16"
}
```

Generate `state_secret`:
```bash
openssl rand -hex 16
```

#### `nerava/backend/posthog`
- PostHog API key (or leave empty if not using PostHog)

## Step 5: Configure terraform.tfvars

1. Copy `terraform.tfvars.example` to `terraform.tfvars`
2. Fill in required values:
   - `acm_certificate_arn` (from Step 2)
   - `route53_zone_id` (from Step 1, or leave empty)
   - `github_repository` (e.g., `your-org/nerava`)
   - `github_oidc_provider_arn` (from Step 3, or leave empty if using access keys)

## Step 6: Initialize and Apply Terraform

```bash
cd infra/terraform
terraform init
terraform plan  # Review changes
terraform apply  # Create infrastructure
```

## Step 7: Build and Push Docker Images

After infrastructure is created, build and push images to ECR:

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
cd ../../backend
docker build -t nerava/backend:latest .
docker tag nerava/backend:latest <ecr-url>/nerava/backend:latest
docker push <ecr-url>/nerava/backend:latest

# Repeat for driver, merchant, admin, landing
# Or use the GitHub Actions workflow (recommended)
```

## Step 8: Update ECS Services

After pushing images, update ECS services to use new images:

```bash
aws ecs update-service --cluster nerava-cluster --service nerava-backend --force-new-deployment --region us-east-1
# Repeat for other services
```

Or trigger the GitHub Actions workflow which will do this automatically.

## Troubleshooting

### Certificate Validation Failing

- Ensure CNAME records are correctly added to Route53
- Wait up to 30 minutes for DNS propagation
- Check certificate status in ACM console

### ECS Tasks Not Starting

- Check CloudWatch Logs for errors
- Verify secrets are correctly formatted (JSON for complex secrets)
- Ensure security groups allow traffic between ALB and ECS tasks
- Check task definition IAM roles have correct permissions

### Database Connection Issues

- Verify RDS security group allows inbound from ECS tasks security group on port 5432
- Check DATABASE_URL secret is correctly formatted
- Ensure RDS is in private subnets (not publicly accessible)

### DNS Not Resolving

- Verify Route53 records point to ALB
- Check ALB DNS name is correct
- Wait for DNS propagation (can take up to 48 hours)

## Next Steps

After manual setup is complete:

1. Run `terraform apply` to create infrastructure
2. Update secrets with real values
3. Build and push Docker images
4. Run migrations (via `scripts/run_migrations.sh`)
5. Verify deployment with smoke tests (`scripts/prod_smoke_test.sh`)

