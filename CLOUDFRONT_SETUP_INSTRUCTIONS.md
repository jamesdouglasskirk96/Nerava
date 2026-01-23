# CloudFront Setup Instructions for nerava.network

## Overview
This guide walks you through setting up a CloudFront distribution for `nerava.network` and `www.nerava.network` to enable HTTPS. The distribution will serve content from your S3 bucket.

## Prerequisites Checklist
- ✅ ACM Certificate: `arn:aws:acm:us-east-1:566287346479:certificate/7ec281ad-9dad-49cd-a173-2f605e0a3910` (Status: ISSUED)
- ✅ S3 Bucket: `nerava.network` (contains your landing page)
- ✅ Route53 Hosted Zone: `Z03087823KHR6VJQ9AGZL` (nerava.network)
- ✅ CloudFront Hosted Zone ID: `Z2FDTNDATAQYW2` (standard for all CloudFront distributions)

---

## Step 1: Create Origin Access Control (OAC)

**Why:** OAC replaces the older Origin Access Identity (OAI) and is required for CloudFront to access your S3 bucket securely.

### Steps:
1. Go to **CloudFront** in AWS Console: https://console.aws.amazon.com/cloudfront/
2. In the left sidebar, click **"Origin access"** → **"Origin access control"**
3. Click **"Create control settings"**
4. Fill in:
   - **Name:** `nerava-network-oac`
   - **Description:** `Origin Access Control for nerava.network S3 bucket`
   - **Signing behavior:** Select **"Sign requests (recommended)"**
   - **Origin type:** Select **"S3"**
   - **Origin access control settings:** Leave default (Signing protocol: sigv4)
5. Click **"Create"**
6. **IMPORTANT:** Copy the **Origin Access Control ID** (looks like `E1234567890ABC`) - you'll need this in Step 2

---

## Step 2: Update S3 Bucket Policy

**Why:** Your S3 bucket needs to allow CloudFront to read objects. The bucket should NOT be publicly accessible.

### Steps:
1. Go to **S3** in AWS Console: https://console.aws.amazon.com/s3/
2. Click on bucket **`nerava.network`**
3. Go to **"Permissions"** tab
4. Scroll to **"Bucket policy"** section
5. Click **"Edit"**
6. Replace the policy with this (replace `YOUR_OAC_ID` with the OAC ID from Step 1, and `YOUR_ACCOUNT_ID` with `566287346479`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::nerava.network/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::566287346479:distribution/*"
        }
      }
    }
  ]
}
```

**Note:** The `/*` at the end of `AWS:SourceArn` allows ANY CloudFront distribution in your account. After creating the distribution, you can update this to the specific distribution ARN for better security.

7. Click **"Save changes"**

---

## Step 3: Create CloudFront Distribution

### Steps:
1. Go to **CloudFront** in AWS Console: https://console.aws.amazon.com/cloudfront/
2. Click **"Create distribution"** (orange button, top right)

### Section 1: Origin Settings

1. **Origin domain:**
   - Click the dropdown
   - Select **`nerava.network.s3.us-east-1.amazonaws.com`** (NOT the website endpoint)
   - ⚠️ **Important:** Use the REST API endpoint, NOT `nerava.network.s3-website-us-east-1.amazonaws.com`

2. **Name:** Auto-filled as `nerava.network.s3.us-east-1.amazonaws.com` (leave as-is)

3. **Origin path:** Leave blank

4. **Origin access:**
   - Select **"Origin access control settings (recommended)"**
   - **Origin access control:** Select the OAC you created in Step 1 (`nerava-network-oac`)

5. **Origin shield:** Leave disabled (not needed for this use case)

6. **Additional settings:** Leave defaults

### Section 2: Default Cache Behavior

1. **Viewer protocol policy:**
   - Select **"Redirect HTTP to HTTPS"** (this enables HTTPS)

2. **Allowed HTTP methods:**
   - Select **"GET, HEAD"** (sufficient for static site)

3. **Cache policy:**
   - Select **"CachingOptimized"** (ID: `658327ea-f89d-4fab-a63d-7e88639e58f6`)
   - This is a managed policy optimized for static content

4. **Origin request policy:** Leave as **"None"** (not needed for S3)

5. **Response headers policy:** Leave as **"None"**

6. **Compress objects automatically:** Check **"Yes"** (enables gzip compression)

### Section 3: Distribution Settings

1. **Price class:**
   - Select **"Use only North America and Europe"** (PriceClass_100)
   - This reduces costs while covering your primary audience

2. **Alternate domain names (CNAMEs):**
   - Click **"Add item"**
   - Enter: `nerava.network`
   - Click **"Add item"** again
   - Enter: `www.nerava.network`
   - You should see both domains listed

3. **Custom SSL certificate:**
   - Select **"Custom SSL certificate"**
   - Click the dropdown
   - Select your certificate: **`nerava.network`** (the one with Status: ISSUED)
   - Certificate ARN should be: `arn:aws:acm:us-east-1:566287346479:certificate/7ec281ad-9dad-49cd-a173-2f605e0a3910`

4. **Default root object:**
   - Enter: `index.html`

5. **Standard logging:** Leave disabled (can enable later if needed)

6. **Comment:**
   - Enter: `CloudFront distribution for nerava.network landing page`

7. **Web Application Firewall (WAF):** Leave disabled (can enable later for security)

8. **HTTP version:** Leave as **"HTTP/2, HTTP/3"**

### Section 4: Custom Error Responses

**Why:** SPA (Single Page Application) routing requires 404 errors to return index.html so client-side routing works.

1. Click **"Create custom error response"**

2. **Error response 1:**
   - **HTTP error code:** `403: Forbidden`
   - **Customize error response:** Check **"Yes"**
   - **Response page path:** `/index.html`
   - **HTTP response code:** `200: OK`
   - **Error caching minimum TTL:** `10` seconds

3. Click **"Create custom error response"** again

4. **Error response 2:**
   - **HTTP error code:** `404: Not Found`
   - **Customize error response:** Check **"Yes"**
   - **Response page path:** `/index.html`
   - **HTTP response code:** `200: OK`
   - **Error caching minimum TTL:** `10` seconds

### Final Step: Create Distribution

1. Scroll to bottom of page
2. Click **"Create distribution"** (orange button)
3. **Wait 10-15 minutes** for distribution to deploy (status will show "In Progress")

---

## Step 4: Verify Distribution Status

### Steps:
1. In CloudFront console, find your new distribution
2. Check **"Status"** column:
   - **"In Progress"** = Still deploying (wait)
   - **"Deployed"** = Ready to use ✅

3. Copy the **Distribution ID** (looks like `E1234567890ABC`)

4. Copy the **Distribution domain name** (looks like `d1234567890abc.cloudfront.net`)

---

## Step 5: Update Route53 DNS Records

**Why:** Point your domain to CloudFront instead of S3 directly.

### Steps:
1. Go to **Route53** in AWS Console: https://console.aws.amazon.com/route53/
2. Click **"Hosted zones"** → **"nerava.network"**
3. Find the **A record** for `nerava.network` (root domain)

### Update Root Domain (nerava.network):

1. Click the **A record** for `nerava.network`
2. Click **"Edit record"**
3. Configure:
   - **Record name:** `nerava.network` (or leave blank if it's the root)
   - **Record type:** `A - Routes traffic to an IPv4 address and some AWS resources`
   - **Alias:** Check **"Yes"**
   - **Route traffic to:**
     - Select **"Alias to CloudFront distribution"**
     - Click dropdown and select your distribution (or paste Distribution domain name)
   - **Evaluate target health:** Leave unchecked
4. Click **"Save changes"**

### Create www Subdomain:

1. Click **"Create record"**
2. Configure:
   - **Record name:** `www`
   - **Record type:** `A - Routes traffic to an IPv4 address and some AWS resources`
   - **Alias:** Check **"Yes"**
   - **Route traffic to:**
     - Select **"Alias to CloudFront distribution"**
     - Select the same distribution as above
   - **Evaluate target health:** Leave unchecked
3. Click **"Create records"**

---

## Step 6: Wait for DNS Propagation

**Timeline:**
- CloudFront deployment: **10-15 minutes**
- DNS propagation: **5-60 minutes** (usually faster)

### Verify Deployment:

1. **Check CloudFront status:**
   ```bash
   aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID --query 'Distribution.Status' --output text
   ```
   Should return: `Deployed`

2. **Test HTTPS:**
   ```bash
   curl -I https://nerava.network
   ```
   Should return: `HTTP/2 200` (not 404 or connection error)

3. **Test www subdomain:**
   ```bash
   curl -I https://www.nerava.network
   ```
   Should return: `HTTP/2 200`

---

## Step 7: Update S3 Bucket Policy (Optional - More Secure)

After your distribution is created, you can restrict the bucket policy to only allow your specific distribution:

1. Go to **CloudFront** → Your distribution
2. Copy the **Distribution ARN** (looks like `arn:aws:cloudfront::566287346479:distribution/E1234567890ABC`)

3. Go to **S3** → `nerava.network` → **Permissions** → **Bucket policy**

4. Replace `/*` in the `AWS:SourceArn` condition with your specific distribution ARN:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::nerava.network/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::566287346479:distribution/YOUR_DISTRIBUTION_ID"
        }
      }
    }
  ]
}
```

---

## Troubleshooting

### Issue: "Your account must be verified"
**Solution:** Try creating the distribution via AWS Console instead of CLI. Sometimes Console bypasses this restriction.

### Issue: "Certificate not found in us-east-1"
**Solution:** CloudFront certificates MUST be in `us-east-1` region. Verify your certificate is in the correct region.

### Issue: "403 Forbidden" when accessing CloudFront URL
**Solution:** 
1. Check S3 bucket policy allows CloudFront
2. Verify OAC is correctly configured on the origin
3. Ensure bucket is NOT publicly accessible (should be private)

### Issue: "404 Not Found" for routes
**Solution:** Verify custom error responses are configured (Step 3, Section 4)

### Issue: DNS not resolving
**Solution:**
1. Wait 5-60 minutes for DNS propagation
2. Check Route53 A record points to CloudFront (not S3)
3. Verify AliasTarget HostedZoneId is `Z2FDTNDATAQYW2`

---

## Verification Checklist

After setup, verify:

- [ ] CloudFront distribution status is "Deployed"
- [ ] `https://nerava.network` returns 200 OK
- [ ] `https://www.nerava.network` returns 200 OK
- [ ] Browser shows padlock icon (HTTPS working)
- [ ] SSL certificate is valid (click padlock → Certificate)
- [ ] Content loads correctly (images, CSS, JS)
- [ ] Client-side routing works (try navigating to a sub-page)

---

## Important Values to Save

After setup, save these for future reference:

- **Distribution ID:** `_________________`
- **Distribution Domain:** `_________________`
- **Distribution ARN:** `_________________`
- **OAC ID:** `_________________`
- **Certificate ARN:** `arn:aws:acm:us-east-1:566287346479:certificate/7ec281ad-9dad-49cd-a173-2f605e0a3910`
- **Route53 Hosted Zone ID:** `Z03087823KHR6VJQ9AGZL`
- **S3 Bucket:** `nerava.network`

---

## Cost Estimate

**CloudFront Pricing (approximate):**
- Data transfer out: $0.085 per GB (first 10 TB/month)
- HTTPS requests: $0.010 per 10,000 requests
- **Estimated monthly cost for low traffic:** $1-5/month

**Note:** CloudFront has a free tier:
- 1 TB data transfer out per month
- 10,000,000 HTTP/HTTPS requests per month

---

## Next Steps After Setup

1. **Invalidate cache** (if you update content):
   - CloudFront → Your distribution → **Invalidations** tab
   - Create invalidation with path: `/*`

2. **Monitor usage:**
   - CloudWatch → Metrics → CloudFront
   - Track requests, data transfer, errors

3. **Set up CloudFront logging** (optional):
   - Distribution → **General** tab → **Logging**
   - Enable access logs to S3 bucket

---

## Quick Reference Commands

```bash
# Check distribution status
aws cloudfront get-distribution --id YOUR_DIST_ID --query 'Distribution.Status'

# Get distribution domain name
aws cloudfront get-distribution --id YOUR_DIST_ID --query 'Distribution.DomainName' --output text

# List all distributions
aws cloudfront list-distributions --query "DistributionList.Items[*].{Id:Id,DomainName:DomainName,Aliases:Aliases.Items}"

# Create invalidation
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

---

## Support Resources

- **AWS CloudFront Documentation:** https://docs.aws.amazon.com/cloudfront/
- **CloudFront Console:** https://console.aws.amazon.com/cloudfront/
- **Route53 Console:** https://console.aws.amazon.com/route53/
- **S3 Console:** https://console.aws.amazon.com/s3/

---

**Last Updated:** January 2026
**Account ID:** 566287346479
**Region:** us-east-1


