# Deployment Rollback Analysis

**Date:** 2026-01-23
**Issue:** Multiple deployments rolling back when switching from VPC to DEFAULT egress

## Problem Summary

When updating App Runner service to use `DEFAULT` egress (to allow Twilio API access), deployments consistently roll back after ~10 minutes.

## Root Cause Analysis

### What We Know:
1. ✅ `/healthz` endpoint doesn't check database (simple liveness probe)
2. ✅ RDS security group allows `0.0.0.0/0` (publicly accessible)
3. ✅ Startup validation passes locally
4. ✅ Image `v20-otp-fix-fixed` exists and is valid
5. ❌ Deployments roll back when egress changes to `DEFAULT`

### Hypothesis:
**With DEFAULT egress, App Runner instances can't reach RDS during startup**, even though RDS is publicly accessible. This could be due to:
- Network routing issues (RDS endpoint resolving to private IP)
- Security group rules blocking despite `0.0.0.0/0`
- Connection timeout during startup validation/initialization

## Solution Options

### Option 1: Keep VPC Egress + Add NAT Gateway (Recommended)
**Pros:**
- App Runner can reach RDS (via VPC)
- App Runner can reach Twilio API (via NAT Gateway)
- No security group changes needed

**Cons:**
- Requires infrastructure changes (NAT Gateway + route table updates)
- Additional cost (~$32/month for NAT Gateway)

**Steps:**
1. Create NAT Gateway in public subnet
2. Update route tables for App Runner subnets (`subnet-0c3e9b306737c3fb2`, `subnet-0dd152da6d977861c`) to route `0.0.0.0/0` → NAT Gateway
3. Keep VPC egress configuration
4. Deploy and test

### Option 2: Make Startup More Lenient
**Pros:**
- No infrastructure changes
- Quick fix

**Cons:**
- Doesn't solve the root cause
- App might start but fail later when accessing DB

**Steps:**
1. Make startup validation non-blocking
2. Defer database connection until first request
3. Update health check to be more lenient

### Option 3: Update RDS Security Group
**Pros:**
- No infrastructure changes

**Cons:**
- App Runner IPs are dynamic (would need to allow all public IPs)
- Security risk
- Doesn't guarantee connectivity

## Recommended Next Steps

1. **Check route tables** for App Runner subnets:
   ```bash
   aws ec2 describe-route-tables \
     --filters "Name=association.subnet-id,Values=subnet-0c3e9b306737c3fb2,subnet-0dd152da6d977861c" \
     --query 'RouteTables[*].Routes[?DestinationCidrBlock==`0.0.0.0/0`]'
   ```

2. **If no NAT Gateway route exists:**
   - Create NAT Gateway in public subnet
   - Update route tables
   - Keep VPC egress
   - Deploy and test

3. **If NAT Gateway route exists:**
   - Check why it's not working
   - Verify NAT Gateway is active
   - Check security groups

## Current Status

- **Service:** Running with `v19-photo-fix` (old image)
- **Egress:** `VPC` (rolled back)
- **Last Operation:** `4dd37102e9c849d4a3c6ad7b929b31f7` → `ROLLBACK_SUCCEEDED`
- **OTP:** Still timing out (VPC blocking Twilio)

## Timeline

| Time | Event |
|------|-------|
| 06:53:14 | Deployment started (DEFAULT egress) |
| 07:12:36 | Rolled back (after ~19 minutes) |
| Current | Service running with VPC egress |

---

**Next Action:** Check route tables and determine if NAT Gateway is needed.




