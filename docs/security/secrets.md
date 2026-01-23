# Nerava Secrets Management

## Where Secrets Live

### Production
- **App Runner:** Environment variables configured in AWS App Runner console
- **GitHub Actions:** Repository secrets in Settings > Secrets and variables > Actions

### Development
- **Local:** `.env` files (never committed, copy from `.env.example`)

## Required Secrets by Service

### Backend (App Runner)
| Secret | Description |
|--------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| JWT_SECRET_KEY | JWT signing key (min 32 chars) |
| TWILIO_ACCOUNT_SID | Twilio account identifier |
| TWILIO_AUTH_TOKEN | Twilio API token |
| SENDGRID_API_KEY | SendGrid email API key |
| SQUARE_ACCESS_TOKEN | Square payment API token |
| GOOGLE_PLACES_API_KEY | Google Places API key |

### Frontend Apps (Build-time)
| Secret | Description |
|--------|-------------|
| VITE_API_BASE_URL | Backend API URL |
| VITE_GOOGLE_PLACES_API_KEY | Google Places (public, restricted by domain) |

### GitHub Actions
| Secret | Description |
|--------|-------------|
| AWS_ACCESS_KEY_ID | AWS deployment credentials |
| AWS_SECRET_ACCESS_KEY | AWS deployment credentials |
| PROD_DATABASE_URL | Production database URL |

## Rotating Compromised Secrets

If secrets were ever committed to git, assume they are compromised and rotate:

### Immediate Actions
1. **JWT_SECRET_KEY:** Generate new 32+ char random string, update App Runner
2. **TWILIO:** Rotate in Twilio Console > API Keys
3. **SENDGRID:** Rotate in SendGrid > Settings > API Keys
4. **SQUARE:** Rotate in Square Developer Dashboard > Credentials
5. **GOOGLE_PLACES_API_KEY:** Rotate in Google Cloud Console > APIs & Services > Credentials
6. **DATABASE_URL:** Change password in AWS RDS, update App Runner

### Git History Cleanup (Optional but Recommended)
If secrets were in git history, consider using `git filter-repo` to remove them:
```bash
# Install git-filter-repo
brew install git-filter-repo

# Remove specific files from all history
git filter-repo --invert-paths --path nerava.key --path nerava-pass.key --path cookies.txt

# Force push (CAUTION: rewrites history)
git push --force --all
```

