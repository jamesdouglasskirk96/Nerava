# Nerava Deployment Quick Start

## One-Command Deployment (After Initial Setup)

```bash
# Set environment variables
export DATABASE_URL="postgresql://postgres:<PASSWORD>@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
export JWT_SECRET="<your-secure-secret>"
export ENV="prod"
export API_BASE_URL="https://api.nerava.network"

# Run deployment scripts in order
./scripts/deploy_api_apprunner.sh && \
./scripts/deploy_static_sites.sh && \
./scripts/deploy_dns.sh && \
./scripts/validate_deployment.sh
```

## Scripts Overview

| Script | Purpose | Time | Output |
|--------|---------|------|--------|
| `deploy_api_apprunner.sh` | Deploy FastAPI backend to App Runner | 5-10 min | Service ARN, Custom Domain |
| `deploy_static_sites.sh` | Build & deploy all frontends to S3/CloudFront | 10-15 min | Distribution IDs |
| `deploy_dns.sh` | Configure Route53 DNS records | 1-2 min | DNS change IDs |
| `validate_deployment.sh` | Test all endpoints | 1-2 min | Test results |

## Prerequisites Checklist

- [ ] AWS CLI configured (`aws configure`)
- [ ] Docker running (`docker ps`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Python 3.9+ installed (`python3 --version`)
- [ ] jq installed (`jq --version`)
- [ ] RDS database accessible
- [ ] ECR repositories exist
- [ ] Route53 hosted zone configured
- [ ] ACM certificate in us-east-1

## Environment Variables

### Required for Backend
```bash
DATABASE_URL="postgresql://postgres:<PASSWORD>@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
JWT_SECRET="<generate-with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'>"
ENV="prod"
```

### Optional (use Secrets Manager)
```bash
JWT_SECRET_SECRET_NAME="nerava/jwt-secret"
GOOGLE_PLACES_API_KEY_SECRET_NAME="nerava/google-places-api-key"
```

## Deployment URLs

After deployment, these URLs should be live:

- **API**: https://api.nerava.network
- **Landing**: https://nerava.network
- **Driver App**: https://app.nerava.network
- **Merchant Portal**: https://merchant.nerava.network
- **Admin Portal**: https://admin.nerava.network
- **Photos**: https://photos.nerava.network

## Troubleshooting Quick Reference

### Backend not starting?
```bash
aws logs tail /aws/apprunner/nerava-api/service --follow
```

### Frontend not loading?
```bash
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

### DNS not resolving?
```bash
dig api.nerava.network
# Wait 5-15 minutes for propagation
```

### CORS errors?
```bash
# Verify ALLOWED_ORIGINS includes all production domains
curl -H "Origin: https://app.nerava.network" -X OPTIONS https://api.nerava.network/v1/auth/otp/start -v
```

## Full Documentation

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for complete documentation.


