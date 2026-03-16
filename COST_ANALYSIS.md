# Nerava Cost Analysis & DDoS Risk Assessment

**Date:** 2026-03-04
**Status:** Living document — update as services/pricing change

---

## Table of Contents

1. [Full Service Inventory](#full-service-inventory)
2. [Monthly Fixed Costs (AWS)](#monthly-fixed-costs-aws)
3. [Usage-Based Costs (APIs)](#usage-based-costs-apis)
4. [Can Nerava Run for Free?](#can-nerava-run-for-free)
5. [Keeping AWS Costs Down](#keeping-aws-costs-down)
6. [DDoS Risk Assessment](#ddos-risk-assessment)
7. [Cost at Scale Projections](#cost-at-scale-projections)

---

## Full Service Inventory

Every paid service, API, and dependency in the Nerava stack:

| Service | Required? | Cost Type | Can Be Free? | Notes |
|---------|-----------|-----------|--------------|-------|
| **AWS App Runner** | Yes | Monthly + usage | No | Backend compute |
| **AWS RDS PostgreSQL** | Yes | Monthly | No | Production database |
| **AWS S3** | Yes | Usage | Practically ($0.05/mo) | Static frontend hosting |
| **AWS CloudFront** | Yes | Usage | Practically ($1-5/mo) | CDN for frontends |
| **AWS CloudWatch** | Yes | Usage | No | Logging — biggest cost surprise |
| **AWS Route53** | Yes | Monthly | No | DNS ($0.50/zone + queries) |
| **AWS NAT Gateways** | Yes* | Monthly | Removable ($64/mo saved) | See cost reduction section |
| **AWS ALB** | Yes* | Monthly | Removable if ECS unused | Load balancer |
| **AWS ECR** | Yes | Usage | Practically ($0.25/mo) | Container registry |
| **AWS Secrets Manager** | Yes | Monthly | No | $0.40/secret × 10 = $4/mo |
| **AWS ACM** | Yes | Free | **Yes** | SSL certificates |
| **Stripe** | Yes | Per-transaction | No | Payment processing |
| **Twilio** | Yes | Per-SMS/verification | **Replaceable** | OTP — biggest API cost |
| **Tesla Fleet API** | Yes | Unknown | Likely free currently | Charging detection |
| **Google Places API** | Yes | Per-call | **Replaceable** | Merchant discovery |
| **PostHog** | Optional | Per-event | **Yes** (self-host or cut) | Analytics |
| **Sentry** | Optional | Per-event | **Yes** (free tier 5K/mo) | Error tracking |
| **Firebase/FCM** | Optional | Free | **Yes** | Android push — free |
| **APNs** | Optional | Free | **Yes** | iOS push — free |
| **Redis** | Optional* | Instance | Removable (use in-memory) | Caching + rate limiting |
| **Apple Sign-In** | Optional | Free | **Yes** | Auth option |
| **Google OAuth** | Optional | Free | **Yes** | Auth option |
| **Smartcar** | Optional | Unknown | Skip it | Non-Tesla EV API |
| **Square** | Optional | Per-transaction | Skip it | Merchant POS |
| **Dwolla** | Optional | Per-ACH | Skip it | Alternative payouts |
| **Plaid** | Optional | Per-link | Skip it | Bank linking |
| **HubSpot** | Optional | Monthly | Skip it | CRM |
| **Fidel CLO** | Optional | Unknown | Skip it | Card-linked offers |
| **NREL** | Optional | Free | **Yes** | Charger data |
| **Overpass/OSM** | Optional | Free | **Yes** | Charger data |

---

## Monthly Fixed Costs (AWS)

These costs are incurred whether you have 0 or 10,000 users:

| Service | Current Config | Monthly Cost | Notes |
|---------|---------------|-------------|-------|
| App Runner | 1 instance (auto-scales) | $25-50 | $0.025/vCPU-hr + $0.0028/GB-hr |
| RDS PostgreSQL | db.t3.micro, 20GB gp3 | $15-18 | $0.017/hr + $2 storage |
| NAT Gateways | 2× (one per AZ) | **$64** | $32/each — biggest fixed cost |
| ALB | 1× (for ECS, may be unused) | **$16-20** | May be removable |
| NLB | 1× (Tesla fleet telemetry) | $16 | Only if telemetry active |
| Route53 | 1 hosted zone | $0.50 | + $0.40/1M queries |
| Secrets Manager | 10 secrets | $4 | $0.40/secret/month |
| ECR | 5 repos, lifecycle 10 images | $0.25 | Negligible |
| CloudWatch Alarms | 10 alarms | $0 | Within free tier |
| ACM | Wildcard cert | $0 | Free |
| **TOTAL FIXED** | | **$141-173/mo** | Before any traffic |

**The $64/mo NAT Gateway cost is the single largest fixed expense.** If your backend doesn't need to reach the internet from private subnets (App Runner handles its own networking), these may be removable.

---

## Usage-Based Costs (APIs)

### Twilio — OTP Verification

| Scale | Logins/Month | Cost/Verification | Monthly Cost |
|-------|-------------|-------------------|-------------|
| 100 users | ~400 | $0.05 | $20 |
| 1K users | ~4,000 | $0.05 | $200 |
| 10K users | ~40,000 | $0.05 | **$2,000** |
| 100K users | ~400,000 | $0.05 | **$20,000** |

**Key insight:** Users don't OTP every time they open the app — JWTs last 7 days. Realistic estimate is ~4 OTPs/user/month (initial login + token refresh). Still, this is the **single most expensive API** at scale.

**How to make it free:** Replace Twilio with email-based OTP using a transactional email service (AWS SES = $0.10/1000 emails = essentially free) or implement WebAuthn/passkeys (completely free, no third-party dependency).

### Google Places API

| Scale | Calls/Month | Cost/1000 | Monthly Cost |
|-------|------------|-----------|-------------|
| 100 users | ~5,000 | $7.00 | $35 (within $200 free tier) |
| 1K users | ~50,000 | $7.00 | **$150** (after free tier) |
| 10K users | ~500,000 | $7.00 | **$3,300** |
| 100K users | ~5,000,000 | $7.00 | **$34,800** |

**Key insight:** Aggressive caching (Redis L2) reduces calls by 60-80%. Real cost at 10K users is ~$660-1,300/mo with good caching.

**How to make it free:** Pre-seed the merchant database from Google Places once, then stop making live API calls. Use OpenStreetMap/Nominatim (free) for geocoding. Merchant data doesn't change frequently — a weekly batch update from your own curated DB costs nothing.

### Stripe

| Item | Rate | Notes |
|------|------|-------|
| Checkout (Nova purchases) | 2.9% + $0.30/txn | Only when drivers buy Nova |
| Connect Express (payouts) | 0.25% + $0.25/payout | Only when drivers withdraw |
| Platform fee | Configurable (currently 20% = 2000 BPS) | Your revenue |

**Key insight:** Stripe costs are **proportional to revenue** — they only cost money when you're making money. This is healthy economics. Can't be eliminated but doesn't cost anything at zero revenue.

### CloudWatch Logs

| Scale | Log Volume/Month | Ingestion Cost | Storage (7-day) |
|-------|-----------------|----------------|-----------------|
| 100 users | ~1 GB | $0.50 | $0.03 |
| 1K users | ~10 GB | $5 | $0.30 |
| 10K users | ~100 GB | **$50** | $3 |
| 100K users | ~1 TB | **$500** | $30 |
| 1M users | ~10 TB | **$5,000** | $300 |

**Key insight:** CloudWatch ingestion ($0.50/GB) is a silent killer. The polling endpoint alone generates most of this. **This is the #1 cost to optimize at scale.**

### CloudFront Data Transfer

| Scale | Transfer/Month | Cost |
|-------|---------------|------|
| 1K users | ~60 GB | $5 |
| 10K users | ~600 GB | **$51** |
| 100K users | ~6 TB | **$510** |

First 1TB/month is $0.085/GB, decreasing at higher tiers.

### Tesla Fleet API

**Currently appears to be free** (no documented per-call pricing from Tesla). However:
- Undocumented rate limits exist
- At 10K drivers polling every 60s = 14.4M calls/day
- Tesla could introduce pricing or throttle at any time
- **Risk:** If Tesla charges even $0.001/call, that's $14,400/day

### Push Notifications (APNs + FCM)

**Both are free.** APNs is included with Apple Developer ($99/year). FCM has a generous free tier (no practical limit for push notifications).

### PostHog Analytics

| Tier | Events/Month | Cost |
|------|-------------|------|
| Free | 1M | $0 |
| Growth | 2M+ | $45+ |

**How to make it free:** Stay under 1M events (doable up to ~5K users), or self-host PostHog (open source, runs on your own infrastructure).

### Sentry Error Tracking

| Tier | Events/Month | Cost |
|------|-------------|------|
| Developer | 5K | $0 |
| Team | 50K | $29 |

**How to make it free:** The free tier (5K events/month) is sufficient unless you have serious error rates. Can also self-host (open source).

---

## Can Nerava Run for Free?

**Goal:** Eliminate all costs except Tesla telemetry infrastructure, AWS hosting, and Stripe transaction fees.

### Services That Can Be Made Free

| Service | Current Cost | Free Alternative | Effort |
|---------|-------------|-----------------|--------|
| **Twilio OTP** | $0.05/verification | AWS SES email OTP ($0.0001/email) or WebAuthn (free) | Medium — change auth flow |
| **Google Places** | $7/1000 calls | Pre-seed DB + OpenStreetMap/Nominatim | Medium — batch seed script |
| **PostHog** | $0-99/mo | Self-host or remove (use CloudWatch metrics) | Low — config change |
| **Sentry** | $0-29/mo | Free tier or self-host | None — already free tier eligible |
| **HubSpot** | $0-400/mo | Remove (disabled by default) | None — already disabled |
| **Redis** | $15-50/mo | Use in-memory caching only (works for single instance) | None — already optional |
| **NAT Gateways** | $64/mo | Remove if not needed by current architecture | Low — test without them |
| **ALB** | $16-20/mo | Remove if not routing to ECS | Low — verify unused |

### Minimum Viable Production Cost

After eliminating optional services and replacing paid APIs with free alternatives:

| Service | Monthly Cost | Can't Avoid |
|---------|-------------|-------------|
| App Runner (1 instance) | $25-50 | Backend must run somewhere |
| RDS PostgreSQL (db.t3.micro) | $15-18 | Need a database |
| CloudWatch Logs (sampled) | $5-10 | Need some logging |
| S3 + CloudFront | $2-5 | Frontend hosting |
| Route53 | $1 | DNS |
| Secrets Manager | $4 | Secret storage |
| ECR | $0.25 | Container images |
| **TOTAL** | **$52-88/mo** | |

Plus:
- Stripe fees: Only when revenue flows (healthy)
- Tesla API: Currently free
- Domain renewal: ~$12/year

**Answer: Yes, Nerava can run for ~$52-88/month** excluding Tesla telemetry, AWS compute, and Stripe fees. The biggest savings come from:
1. Replacing Twilio with email OTP or WebAuthn (saves $200-20,000/mo at scale)
2. Pre-seeding merchant data instead of live Google Places calls (saves $150-34,000/mo at scale)
3. Removing NAT Gateways if unused (saves $64/mo)
4. Removing unused ALB (saves $16-20/mo)
5. Self-hosting or cutting PostHog (saves $0-99/mo)

---

## Keeping AWS Costs Down

### Immediate Wins (Do Now)

| Action | Savings | Effort |
|--------|---------|--------|
| **Remove NAT Gateways** if App Runner doesn't use them | $64/mo | 1 hour — test, then delete |
| **Remove ALB** if not routing to ECS services | $16-20/mo | 1 hour — verify, then delete |
| **Reduce CloudWatch log retention** from 7 days to 1 day | 85% log storage savings | 5 min — Terraform change |
| **Skip logging health checks** (`/healthz`, `/readyz`) | ~30% log volume reduction | 30 min — middleware filter |
| **Sample poll endpoint logs** (log 1-in-10 successful polls) | ~60% log volume reduction | 30 min — middleware change |
| **Set AWS Budget alerts** at $100, $200, $500 | $0 (free) | 15 min — AWS console |

### Medium-Term Optimizations

| Action | Savings | Effort |
|--------|---------|--------|
| **Replace Twilio with AWS SES email OTP** | $200-20,000/mo | 1-2 days — new auth flow |
| **Pre-seed merchant DB, stop live Google Places calls** | $150-34,000/mo | 1 day — batch script + cache |
| **Add VPC Gateway Endpoints for S3** | Reduces NAT data transfer fees | 30 min — Terraform |
| **Enable RDS reserved instances** (1-year commitment) | ~40% RDS savings | 5 min — AWS console |
| **Switch to ARM-based App Runner** (if supported) | ~20% compute savings | Test compatibility |

### Long-Term Architecture Changes

| Action | Savings | Effort |
|--------|---------|--------|
| **Replace polling with Tesla webhooks** | Eliminates majority of compute + log cost | Significant — architecture change |
| **Move to ECS with Spot instances** | 50-70% compute savings vs App Runner | Migration project |
| **Archive old session data to S3 Glacier** | $0.004/GB vs $0.10/GB RDS storage | 1 day — scheduled Lambda |
| **Implement proper metrics** instead of log-based monitoring | Eliminate most CloudWatch log costs | 1 day — Prometheus/Grafana |

---

## DDoS Risk Assessment

### Current Protection

| Layer | Protection | Status |
|-------|-----------|--------|
| **L3/L4 (Network)** | AWS Shield Standard | **Free, automatic** on CloudFront + ALB |
| **L7 (Application)** | AWS WAF | **NOT configured** |
| **Application Rate Limiting** | Redis-backed token bucket | **Active** — 120 req/min global |
| **Endpoint-Specific Limits** | Per-path rate limits | **Active** — 32 endpoint rules |
| **CloudFront Caching** | Static asset protection | **Active** — frontends protected |

### What Happens During a DDoS Attack Right Now

#### Scenario 1: L3/L4 Volumetric Attack (SYN flood, UDP flood)
- **Protection:** AWS Shield Standard (free) handles this automatically
- **Cost impact:** Minimal — Shield absorbs the traffic before it hits your services
- **Risk level:** LOW

#### Scenario 2: L7 Application Attack on Static Frontends (CloudFront)
- **Protection:** CloudFront absorbs the traffic, serves cached content
- **Cost impact:** CloudFront charges per request ($0.0075/10K requests) and per GB transferred
  - 100M requests = $75
  - 10TB transfer = $850
  - **Worst case: $500-2,000** for a sustained attack on static assets
- **Risk level:** MEDIUM — costs are bounded by CloudFront pricing tiers

#### Scenario 3: L7 Application Attack on Backend API (App Runner) — THE REAL RISK

**This is where you're vulnerable.**

- **No WAF** means every request hits App Runner
- App Runner auto-scales based on traffic → **costs scale with attack volume**
- Rate limiting is **inside the application** — it only fires after the request reaches your code
- Each App Runner instance costs ~$0.025/vCPU-hour

**Attack cost projection:**

| Attack Intensity | Requests/Second | App Runner Instances | Hourly Cost | Daily Cost |
|-----------------|-----------------|---------------------|-------------|------------|
| Light | 1,000 | 3-5 | $0.13-0.22 | $3-5 |
| Medium | 10,000 | 10-15 | $0.44-0.66 | **$11-16** |
| Heavy | 100,000 | 25 (max) | $1.10 | **$26** |
| Sustained heavy (30 days) | 100,000 | 25 (max) | $1.10 | **$792/mo** |

**Plus CloudWatch log costs from attack traffic:**

| Attack Duration | Log Volume | CloudWatch Cost |
|----------------|-----------|-----------------|
| 1 hour at 100K req/s | ~180 GB | **$90** |
| 24 hours at 100K req/s | ~4.3 TB | **$2,150** |
| 7 days at 100K req/s | ~30 TB | **$15,000** |

**Total worst-case DDoS cost (7-day sustained L7 attack):**
- App Runner scaling: ~$185
- CloudWatch logs: **~$15,000** ← THIS is the real danger
- RDS connections exhausted → potential downtime
- **Total: ~$15,000-16,000**

#### Scenario 4: Targeted API Abuse (OTP/Auth Endpoints)
- Rate limited to 3-5 req/min per IP
- BUT attacker with many IPs can bypass this
- **Twilio cost risk:** Each OTP attempt costs $0.05
  - 100K fake OTP requests = **$5,000 in Twilio charges**
  - Rate limit (3/min/IP) × 10,000 IPs = 30,000/min = **$1,500/min in Twilio**
- **Risk level:** HIGH — Twilio costs can spiral fast

### How to Protect Against DDoS (Recommended Actions)

#### Priority 1: Stop the Bleeding (Do Today)

1. **Add AWS WAF to App Runner / ALB** ($5/mo base + $0.60/rule)
   - Rate-based rule: Block IPs exceeding 2,000 requests per 5 minutes
   - Geographic restriction: US-only (if applicable)
   - Known bad bot blocking (AWS Managed Rules)
   - **This alone prevents 90% of L7 attacks**

2. **Set AWS Budget alert at $200/month**
   - SNS notification when costs spike
   - Catches runaway scaling within hours

3. **Reduce CloudWatch log retention to 1 day during attack**
   - Can be changed in seconds via AWS console
   - Prevents log ingestion costs from spiraling

#### Priority 2: Harden the Application (This Week)

4. **Add IP-based rate limiting at infrastructure level** (not just application)
   - AWS WAF rate-based rules fire before traffic reaches App Runner
   - Saves compute + log costs

5. **Cap App Runner max instances** to a known affordable number
   - Currently defaults to 25 (the platform max)
   - Set to 5-10 for predictable worst-case cost
   - Trade: May lose availability under legitimate load spikes

6. **Disable CloudWatch logging for rate-limited (429) responses**
   - Attack traffic that gets 429'd still generates logs
   - Skip logging these entirely

7. **Add CAPTCHA or proof-of-work before OTP**
   - Prevents automated OTP abuse
   - Turnstile (Cloudflare, free) or reCAPTCHA (Google, free)

#### Priority 3: Long-Term Resilience

8. **Move to CloudFront → API Gateway → Lambda/ECS**
   - CloudFront absorbs L7 DDoS
   - API Gateway has built-in throttling ($3.50/million requests)
   - Eliminates App Runner auto-scaling risk

9. **Replace Twilio with email OTP or WebAuthn**
   - Eliminates the OTP cost attack vector entirely
   - Email OTP via SES: $0.10/1000 emails (1000x cheaper than Twilio)

---

## Cost at Scale Projections

### Current Architecture (No Optimizations)

| | 1K Users | 10K Users | 100K Users | 1M Users |
|---|---------|-----------|------------|----------|
| **AWS Fixed** | $141 | $141 | $141 | $141 |
| **App Runner** | $50 | $150 | $500 | $1,000+ |
| **RDS** | $18 | $50 | $200 | $500 |
| **CloudWatch** | $5 | $50 | $500 | **$5,000** |
| **CloudFront** | $2 | $51 | $510 | $2,000 |
| **Twilio** | $200 | **$2,000** | **$20,000** | **$200,000** |
| **Google Places** | $0 | **$1,300** | **$13,000** | **$130,000** |
| **PostHog** | $0 | $45 | $200 | $500 |
| **Stripe** | Revenue % | Revenue % | Revenue % | Revenue % |
| **TOTAL** | **$416** | **$3,787** | **$35,051** | **$339,141** |

### Optimized Architecture (Free Alternatives Applied)

| | 1K Users | 10K Users | 100K Users | 1M Users |
|---|---------|-----------|------------|----------|
| **AWS Fixed** | $57* | $57* | $57* | $57* |
| **App Runner** | $50 | $150 | $500 | $1,000+ |
| **RDS** | $18 | $50 | $200 | $500 |
| **CloudWatch (sampled)** | $1 | $5 | $50 | **$500** |
| **CloudFront** | $2 | $51 | $510 | $2,000 |
| **Email OTP (SES)** | $0.04 | $0.40 | $4 | $40 |
| **Google Places** | $0 | $0 | $0 | $0 |
| **PostHog** | $0 | $0 | $0 | $0 |
| **Stripe** | Revenue % | Revenue % | Revenue % | Revenue % |
| **TOTAL** | **$128** | **$313** | **$1,321** | **$4,097** |

*\* After removing NAT Gateways ($64) and unused ALB ($20)*

**Savings at 100K users: $33,730/month (96% reduction)**
**Savings at 1M users: $335,044/month (99% reduction)**

The two biggest wins are replacing Twilio ($200K/mo → $40/mo) and eliminating live Google Places calls ($130K/mo → $0/mo).

---

## Quick Reference: What's Actually Costing Money Today

At current scale (~small user base), your monthly bill is approximately:

| Item | Est. Cost |
|------|-----------|
| NAT Gateways | $64 |
| App Runner | $25-50 |
| RDS | $15-18 |
| ALB (if active) | $16-20 |
| NLB (fleet telemetry) | $16 |
| Twilio | $20-200 (depends on logins) |
| CloudWatch | $5-10 |
| Secrets Manager | $4 |
| Everything else | <$10 |
| **TOTAL** | **~$175-390/mo** |

The single most impactful immediate action: **remove NAT Gateways if App Runner doesn't need them** (saves $64/mo, ~20-35% of your current bill).
