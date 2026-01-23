# CloudFront Setup - Quick Checklist

## Pre-Setup Info
- **ACM Certificate ARN:** `arn:aws:acm:us-east-1:566287346479:certificate/7ec281ad-9dad-49cd-a173-2f605e0a3910`
- **S3 Bucket:** `nerava.network`
- **Route53 Zone ID:** `Z03087823KHR6VJQ9AGZL`
- **CloudFront Hosted Zone ID:** `Z2FDTNDATAQYW2` (always the same)

---

## Step 1: Create Origin Access Control (OAC)
- [ ] Go to CloudFront → Origin access → Origin access control
- [ ] Click "Create control settings"
- [ ] Name: `nerava-network-oac`
- [ ] Signing behavior: "Sign requests (recommended)"
- [ ] Origin type: "S3"
- [ ] Click "Create"
- [ ] **COPY OAC ID:** `_________________`

---

## Step 2: Update S3 Bucket Policy
- [ ] Go to S3 → `nerava.network` → Permissions → Bucket policy
- [ ] Click "Edit"
- [ ] Paste the policy (see full instructions)
- [ ] Save changes

---

## Step 3: Create CloudFront Distribution

### Origin Settings
- [ ] Origin domain: `nerava.network.s3.us-east-1.amazonaws.com` (REST API endpoint)
- [ ] Origin access: "Origin access control settings"
- [ ] Select OAC: `nerava-network-oac`

### Default Cache Behavior
- [ ] Viewer protocol: "Redirect HTTP to HTTPS"
- [ ] Allowed methods: "GET, HEAD"
- [ ] Cache policy: "CachingOptimized"
- [ ] Compress: "Yes"

### Distribution Settings
- [ ] Price class: "Use only North America and Europe"
- [ ] CNAMEs: Add `nerava.network` and `www.nerava.network`
- [ ] SSL certificate: Select `nerava.network` (ISSUED)
- [ ] Default root: `index.html`
- [ ] Comment: "CloudFront for nerava.network"

### Custom Error Responses
- [ ] 403 → `/index.html` → 200
- [ ] 404 → `/index.html` → 200

### Create
- [ ] Click "Create distribution"
- [ ] **COPY Distribution ID:** `_________________`
- [ ] **COPY Distribution Domain:** `_________________`
- [ ] Wait 10-15 minutes for "Deployed" status

---

## Step 4: Update Route53

### Root Domain (nerava.network)
- [ ] Route53 → nerava.network → Edit A record
- [ ] Alias: Yes
- [ ] Route to: CloudFront distribution
- [ ] Select your distribution
- [ ] Save

### www Subdomain
- [ ] Create new A record
- [ ] Name: `www`
- [ ] Alias: Yes
- [ ] Route to: CloudFront distribution
- [ ] Select same distribution
- [ ] Create

---

## Step 5: Verify
- [ ] Wait 5-60 minutes for DNS propagation
- [ ] Test: `curl -I https://nerava.network` → Should return 200
- [ ] Test: `curl -I https://www.nerava.network` → Should return 200
- [ ] Browser shows padlock icon ✅

---

## Troubleshooting Quick Fixes

**403 Forbidden:**
- Check S3 bucket policy allows CloudFront
- Verify OAC is configured on origin

**404 Not Found:**
- Verify custom error responses are set (403/404 → index.html)

**Certificate Error:**
- Ensure certificate is in `us-east-1` region
- Verify certificate covers `nerava.network` and `*.nerava.network`

**DNS Not Resolving:**
- Wait longer (up to 60 minutes)
- Verify Route53 A record uses AliasTarget (not CNAME)
- Check HostedZoneId is `Z2FDTNDATAQYW2`

---

## After Setup - Save These Values

- Distribution ID: `_________________`
- Distribution Domain: `_________________`
- Distribution ARN: `_________________`
- OAC ID: `_________________`

---

**See `CLOUDFRONT_SETUP_INSTRUCTIONS.md` for detailed explanations.**


