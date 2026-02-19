# Add NAT Gateway for OTP - VPC Networking Fix

**Date:** 2026-01-23
**Priority:** CRITICAL - Blocking all OTP/SMS functionality
**Root Cause:** VPC subnets have no outbound internet route

---

## Problem Summary

App Runner deployment keeps rolling back because:

| Egress Mode | RDS Access | Twilio Access | Result |
|-------------|------------|---------------|--------|
| VPC | ✅ Works | ❌ Timeout | OTP fails |
| DEFAULT | ❌ Fails | ✅ Works | Deployment rollback |

**Solution:** Add NAT Gateway so VPC egress can reach BOTH RDS and Twilio.

---

## VPC Details

```
VPC ID: vpc-0070057532e81973b
App Runner Subnets:
  - subnet-0c3e9b306737c3fb2 (us-east-1a)
  - subnet-0dd152da6d977861c (us-east-1d)
RDS: nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com
```

---

## Step 1: Find or Create Internet Gateway

```bash
# Check if VPC has an Internet Gateway
aws ec2 describe-internet-gateways \
  --filters "Name=attachment.vpc-id,Values=vpc-0070057532e81973b" \
  --query 'InternetGateways[*].InternetGatewayId' \
  --output text
```

If empty, create one:
```bash
# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)
echo "Created IGW: $IGW_ID"

# Attach to VPC
aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id vpc-0070057532e81973b
```

---

## Step 2: Create Elastic IP for NAT Gateway

```bash
# Allocate Elastic IP
EIP_ALLOC=$(aws ec2 allocate-address \
  --domain vpc \
  --query 'AllocationId' \
  --output text)
echo "Allocated EIP: $EIP_ALLOC"
```

---

## Step 3: Create NAT Gateway

Create NAT Gateway in one of the public subnets:

```bash
# Create NAT Gateway in subnet-0c3e9b306737c3fb2 (us-east-1a)
NAT_GW_ID=$(aws ec2 create-nat-gateway \
  --subnet-id subnet-0c3e9b306737c3fb2 \
  --allocation-id $EIP_ALLOC \
  --query 'NatGateway.NatGatewayId' \
  --output text)
echo "Created NAT Gateway: $NAT_GW_ID"

# Wait for NAT Gateway to become available (takes 1-2 minutes)
echo "Waiting for NAT Gateway to become available..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID
echo "NAT Gateway is available!"
```

---

## Step 4: Update Route Tables

Find the route tables for the App Runner subnets and add NAT Gateway route:

```bash
# Find route tables for App Runner subnets
RT_1=$(aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=subnet-0c3e9b306737c3fb2" \
  --query 'RouteTables[0].RouteTableId' \
  --output text)

RT_2=$(aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=subnet-0dd152da6d977861c" \
  --query 'RouteTables[0].RouteTableId' \
  --output text)

echo "Route Table 1: $RT_1"
echo "Route Table 2: $RT_2"
```

If route tables are "None" or empty, the subnets use the main route table:
```bash
# Get main route table for VPC
MAIN_RT=$(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-0070057532e81973b" "Name=association.main,Values=true" \
  --query 'RouteTables[0].RouteTableId' \
  --output text)
echo "Main Route Table: $MAIN_RT"
```

Add NAT Gateway route for outbound internet:
```bash
# Add route to NAT Gateway (use the correct route table ID)
# Replace ROUTE_TABLE_ID with actual ID from above

aws ec2 create-route \
  --route-table-id ROUTE_TABLE_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_ID

echo "Route added: 0.0.0.0/0 -> NAT Gateway"
```

**Note:** If there's already a route for `0.0.0.0/0`, use `replace-route` instead:
```bash
aws ec2 replace-route \
  --route-table-id ROUTE_TABLE_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_ID
```

---

## Step 5: Verify NAT Gateway Setup

```bash
# Verify NAT Gateway is available
aws ec2 describe-nat-gateways \
  --nat-gateway-ids $NAT_GW_ID \
  --query 'NatGateways[0].{State:State,SubnetId:SubnetId}'

# Verify route exists
aws ec2 describe-route-tables \
  --route-table-ids ROUTE_TABLE_ID \
  --query 'RouteTables[0].Routes[?DestinationCidrBlock==`0.0.0.0/0`]'
```

---

## Step 6: Deploy with VPC Egress

Now deploy with VPC egress (which can reach both RDS and Twilio via NAT):

```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --network-configuration '{
    "EgressConfiguration": {
      "EgressType": "VPC",
      "VpcConnectorArn": "arn:aws:apprunner:us-east-1:566287346479:vpcconnector/nerava-vpc-connector/1/b07c0001ddf341b8b426d7fa83d93ad8"
    }
  }' \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v20-otp-fix-fixed",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {"Port": "8000"}
    },
    "AutoDeploymentsEnabled": false,
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::566287346479:role/AppRunnerECRAccessRole"
    }
  }'
```

---

## Step 7: Monitor Deployment

```bash
# Check status every 2 minutes
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0].{Status:Status,Started:StartedAt}' \
  --output table
```

---

## Step 8: Test OTP

Once deployment succeeds:

```bash
# Health check
curl -s https://api.nerava.network/health

# OTP test
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 45
```

**Expected:** `{"otp_sent":true}` and SMS received on phone.

---

## Cost Estimate

| Resource | Cost |
|----------|------|
| NAT Gateway | ~$0.045/hour (~$32/month) |
| Data processing | $0.045/GB |
| Elastic IP | Free (if attached to NAT GW) |

**Total estimated:** ~$35-50/month depending on traffic

---

## Alternative: Use AWS PrivateLink for Twilio

If cost is a concern, Twilio supports AWS PrivateLink which avoids NAT Gateway costs. However, this requires:
1. Twilio Enterprise plan
2. VPC Endpoint setup
3. More complex configuration

NAT Gateway is simpler and works immediately.

---

## Rollback Plan

If NAT Gateway causes issues:

```bash
# Delete NAT Gateway
aws ec2 delete-nat-gateway --nat-gateway-id $NAT_GW_ID

# Wait for deletion
aws ec2 wait nat-gateway-deleted --nat-gateway-ids $NAT_GW_ID

# Release Elastic IP
aws ec2 release-address --allocation-id $EIP_ALLOC

# Remove route (replace with IGW if needed)
aws ec2 delete-route \
  --route-table-id ROUTE_TABLE_ID \
  --destination-cidr-block 0.0.0.0/0
```

---

## Complete Script

Save as `scripts/setup-nat-gateway.sh`:

```bash
#!/bin/bash
set -e

VPC_ID="vpc-0070057532e81973b"
SUBNET_ID="subnet-0c3e9b306737c3fb2"  # Public subnet for NAT GW

echo "=== Setting up NAT Gateway for Nerava VPC ==="

# Step 1: Check for Internet Gateway
echo "Checking for Internet Gateway..."
IGW_ID=$(aws ec2 describe-internet-gateways \
  --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
  --query 'InternetGateways[0].InternetGatewayId' \
  --output text)

if [ "$IGW_ID" = "None" ] || [ -z "$IGW_ID" ]; then
  echo "Creating Internet Gateway..."
  IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
  aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
fi
echo "Internet Gateway: $IGW_ID"

# Step 2: Allocate Elastic IP
echo "Allocating Elastic IP..."
EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
echo "Elastic IP Allocation: $EIP_ALLOC"

# Step 3: Create NAT Gateway
echo "Creating NAT Gateway..."
NAT_GW_ID=$(aws ec2 create-nat-gateway \
  --subnet-id $SUBNET_ID \
  --allocation-id $EIP_ALLOC \
  --query 'NatGateway.NatGatewayId' \
  --output text)
echo "NAT Gateway: $NAT_GW_ID"

echo "Waiting for NAT Gateway to become available (1-2 minutes)..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID
echo "NAT Gateway is available!"

# Step 4: Get main route table
echo "Finding route table..."
MAIN_RT=$(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=association.main,Values=true" \
  --query 'RouteTables[0].RouteTableId' \
  --output text)
echo "Main Route Table: $MAIN_RT"

# Step 5: Add NAT Gateway route
echo "Adding route to NAT Gateway..."
aws ec2 create-route \
  --route-table-id $MAIN_RT \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_ID 2>/dev/null || \
aws ec2 replace-route \
  --route-table-id $MAIN_RT \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_ID

echo ""
echo "=== NAT Gateway Setup Complete ==="
echo "NAT Gateway ID: $NAT_GW_ID"
echo "Elastic IP Allocation: $EIP_ALLOC"
echo "Route Table: $MAIN_RT"
echo ""
echo "Now deploy the backend with VPC egress:"
echo "aws apprunner update-service ..."
```

---

## Success Checklist

- [ ] Elastic IP allocated
- [ ] NAT Gateway created and available
- [ ] Route table updated with `0.0.0.0/0 -> NAT Gateway`
- [ ] Deployment succeeded (not rolled back)
- [ ] Health check: `{"ok":true}`
- [ ] OTP request: `{"otp_sent":true}`
- [ ] SMS received on +17133056318

---

**End of NAT Gateway Setup Prompt**
