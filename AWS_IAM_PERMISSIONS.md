# AWS IAM Permissions Required for App Runner Deployment

This document lists all AWS permissions needed for the Nerava App Runner deployment.

## Summary

The user needs permissions for:
- **App Runner** - Create, update, and manage services
- **ECR** - Push Docker images
- **RDS** - Create and manage PostgreSQL database
- **ElastiCache** - Create and manage Redis cluster
- **CloudFront** - Create distribution for frontend
- **S3** - Deploy frontend files
- **CloudWatch Logs** - View service logs
- **EC2/VPC** - Network configuration (if needed)

## IAM Policy JSON

Here's a complete IAM policy with all required permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AppRunnerPermissions",
      "Effect": "Allow",
      "Action": [
        "apprunner:CreateService",
        "apprunner:UpdateService",
        "apprunner:DeleteService",
        "apprunner:DescribeService",
        "apprunner:ListServices",
        "apprunner:ListOperations",
        "apprunner:StartDeployment",
        "apprunner:PauseService",
        "apprunner:ResumeService",
        "apprunner:TagResource",
        "apprunner:UntagResource",
        "apprunner:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ECRPermissions",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:CreateRepository",
        "ecr:DescribeImages",
        "ecr:ListImages"
      ],
      "Resource": "*"
    },
    {
      "Sid": "RDSPermissions",
      "Effect": "Allow",
      "Action": [
        "rds:CreateDBInstance",
        "rds:DescribeDBInstances",
        "rds:ModifyDBInstance",
        "rds:DeleteDBInstance",
        "rds:CreateDBSubnetGroup",
        "rds:DescribeDBSubnetGroups",
        "rds:ModifyDBSubnetGroup",
        "rds:DeleteDBSubnetGroup",
        "rds:CreateDBParameterGroup",
        "rds:DescribeDBParameterGroups",
        "rds:ModifyDBParameterGroup",
        "rds:DeleteDBParameterGroup",
        "rds:AddTagsToResource",
        "rds:ListTagsForResource",
        "rds:RemoveTagsFromResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ElastiCachePermissions",
      "Effect": "Allow",
      "Action": [
        "elasticache:CreateReplicationGroup",
        "elasticache:DescribeReplicationGroups",
        "elasticache:ModifyReplicationGroup",
        "elasticache:DeleteReplicationGroup",
        "elasticache:CreateCacheCluster",
        "elasticache:DescribeCacheClusters",
        "elasticache:ModifyCacheCluster",
        "elasticache:DeleteCacheCluster",
        "elasticache:DescribeCacheSubnetGroups",
        "elasticache:CreateCacheSubnetGroup",
        "elasticache:ModifyCacheSubnetGroup",
        "elasticache:DeleteCacheSubnetGroup",
        "elasticache:AddTagsToResource",
        "elasticache:ListTagsForResource",
        "elasticache:RemoveTagsFromResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudFrontPermissions",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateDistribution",
        "cloudfront:GetDistribution",
        "cloudfront:UpdateDistribution",
        "cloudfront:DeleteDistribution",
        "cloudfront:ListDistributions",
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
        "cloudfront:ListInvalidations",
        "cloudfront:CreateOriginAccessControl",
        "cloudfront:GetOriginAccessControl",
        "cloudfront:UpdateOriginAccessControl",
        "cloudfront:DeleteOriginAccessControl",
        "cloudfront:ListOriginAccessControls",
        "cloudfront:TagResource",
        "cloudfront:UntagResource",
        "cloudfront:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3Permissions",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetObjectVersion",
        "s3:PutObjectAcl",
        "s3:GetBucketAcl",
        "s3:PutBucketAcl"
      ],
      "Resource": [
        "arn:aws:s3:::nerava-frontend-*",
        "arn:aws:s3:::nerava-frontend-*/*"
      ]
    },
    {
      "Sid": "CloudWatchLogsPermissions",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "logs:PutLogEvents",
        "logs:CreateLogStream",
        "logs:TagLogGroup"
      ],
      "Resource": [
        "arn:aws:logs:us-east-1:*:log-group:/aws/apprunner/*"
      ]
    },
    {
      "Sid": "EC2VPCReadPermissions",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeInternetGateways",
        "ec2:DescribeRouteTables",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DescribeAvailabilityZones"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMReadPermissions",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:ListRoles",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies"
      ],
      "Resource": [
        "arn:aws:iam::*:role/AppRunnerECRAccessRole",
        "arn:aws:iam::*:role/service-role/*"
      ]
    }
  ]
}
```

## Permission Breakdown by Service

### 1. App Runner (Required)
**Purpose**: Create, update, and manage App Runner services

**Minimum Required**:
- `apprunner:DescribeService` - Check service status
- `apprunner:UpdateService` - Update service configuration
- `apprunner:ListOperations` - Check operation status

**Full Set** (recommended):
- `apprunner:CreateService` - Create new services
- `apprunner:UpdateService` - Update existing services
- `apprunner:DescribeService` - Get service details
- `apprunner:ListServices` - List all services
- `apprunner:ListOperations` - List service operations
- `apprunner:StartDeployment` - Trigger deployments
- `apprunner:PauseService` - Pause service
- `apprunner:ResumeService` - Resume service

### 2. ECR (Required)
**Purpose**: Push Docker images to Elastic Container Registry

**Minimum Required**:
- `ecr:GetAuthorizationToken` - Get login token
- `ecr:PutImage` - Push images
- `ecr:BatchCheckLayerAvailability` - Check layers
- `ecr:InitiateLayerUpload` - Start upload
- `ecr:UploadLayerPart` - Upload parts
- `ecr:CompleteLayerUpload` - Finish upload

**Full Set** (recommended):
- All minimum permissions plus:
- `ecr:DescribeRepositories` - List repositories
- `ecr:CreateRepository` - Create new repositories
- `ecr:DescribeImages` - List images
- `ecr:ListImages` - List image tags

### 3. RDS (Required for Production)
**Purpose**: Create and manage PostgreSQL database

**Minimum Required**:
- `rds:CreateDBInstance` - Create database
- `rds:DescribeDBInstances` - Get database info
- `rds:ModifyDBInstance` - Update database

**Full Set** (recommended):
- All minimum permissions plus:
- `rds:DeleteDBInstance` - Delete database
- `rds:CreateDBSubnetGroup` - Create subnet groups
- `rds:DescribeDBSubnetGroups` - List subnet groups
- `rds:ModifyDBSubnetGroup` - Update subnet groups
- `rds:CreateDBParameterGroup` - Create parameter groups
- `rds:DescribeDBParameterGroups` - List parameter groups

### 4. ElastiCache (Required for Production)
**Purpose**: Create and manage Redis cluster

**Minimum Required**:
- `elasticache:CreateReplicationGroup` - Create Redis cluster
- `elasticache:DescribeReplicationGroups` - Get cluster info
- `elasticache:ModifyReplicationGroup` - Update cluster

**Full Set** (recommended):
- All minimum permissions plus:
- `elasticache:DeleteReplicationGroup` - Delete cluster
- `elasticache:CreateCacheCluster` - Create cache cluster
- `elasticache:DescribeCacheClusters` - List clusters
- `elasticache:DescribeCacheSubnetGroups` - List subnet groups
- `elasticache:CreateCacheSubnetGroup` - Create subnet groups

### 5. CloudFront (Optional - for Frontend)
**Purpose**: Create CDN distribution for frontend

**Minimum Required**:
- `cloudfront:CreateDistribution` - Create distribution
- `cloudfront:GetDistribution` - Get distribution info
- `cloudfront:ListDistributions` - List distributions
- `cloudfront:CreateInvalidation` - Invalidate cache

**Full Set** (recommended):
- All minimum permissions plus:
- `cloudfront:UpdateDistribution` - Update distribution
- `cloudfront:DeleteDistribution` - Delete distribution
- `cloudfront:CreateOriginAccessControl` - Create OAC
- `cloudfront:GetOriginAccessControl` - Get OAC info

### 6. S3 (Required for Frontend)
**Purpose**: Deploy frontend files

**Minimum Required**:
- `s3:PutObject` - Upload files
- `s3:GetObject` - Download files
- `s3:ListBucket` - List bucket contents
- `s3:GetBucketLocation` - Get bucket region

**Full Set** (recommended):
- All minimum permissions plus:
- `s3:CreateBucket` - Create buckets
- `s3:DeleteBucket` - Delete buckets
- `s3:DeleteObject` - Delete files
- `s3:PutObjectAcl` - Set object ACLs

### 7. CloudWatch Logs (Recommended)
**Purpose**: View App Runner service logs for debugging

**Minimum Required**:
- `logs:DescribeLogGroups` - List log groups
- `logs:DescribeLogStreams` - List log streams
- `logs:GetLogEvents` - Read log events
- `logs:FilterLogEvents` - Filter/search logs

**Full Set** (recommended):
- All minimum permissions plus:
- `logs:CreateLogGroup` - Create log groups
- `logs:CreateLogStream` - Create log streams
- `logs:PutLogEvents` - Write logs (if needed)

### 8. EC2/VPC (Required for RDS/ElastiCache)
**Purpose**: Read VPC/subnet information for database setup

**Minimum Required**:
- `ec2:DescribeVpcs` - List VPCs
- `ec2:DescribeSubnets` - List subnets
- `ec2:DescribeSecurityGroups` - List security groups
- `ec2:DescribeAvailabilityZones` - List AZs

### 9. IAM (Read-only, Recommended)
**Purpose**: Verify App Runner service roles exist

**Minimum Required**:
- `iam:GetRole` - Get role details
- `iam:ListRoles` - List roles

## How to Apply Permissions

### Option 1: Attach Managed Policy (if available)
AWS doesn't provide managed policies for all these services, so you'll need a custom policy.

### Option 2: Create Custom Policy

1. **Go to IAM Console**:
   - Navigate to IAM → Policies → Create Policy

2. **Use JSON Editor**:
   - Copy the JSON policy above
   - Paste into the JSON editor

3. **Review and Create**:
   - Name: `NeravaAppRunnerDeploymentPolicy`
   - Description: `Full permissions for Nerava App Runner deployment`

4. **Attach to User/Role**:
   - Go to Users → Select your user → Add permissions
   - Attach the custom policy

### Option 3: Use AWS CLI

```bash
# Create the policy
aws iam create-policy \
    --policy-name NeravaAppRunnerDeploymentPolicy \
    --policy-document file://nerava-apprunner-policy.json

# Attach to user
aws iam attach-user-policy \
    --user-name YOUR_USERNAME \
    --policy-arn arn:aws:iam::ACCOUNT_ID:policy/NeravaAppRunnerDeploymentPolicy
```

## Minimal Permissions (For Testing Only)

If you only want to update the existing App Runner service (not create RDS/Redis):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "apprunner:DescribeService",
        "apprunner:UpdateService",
        "apprunner:ListOperations",
        "ecr:GetAuthorizationToken",
        "ecr:PutImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

## Current Permission Status

Based on `AWS_DEPLOYMENT_STATUS.md`:

✅ **Working**:
- App Runner (can describe/update)
- ECR (can push images)
- S3 (can deploy frontend)

❌ **Missing**:
- RDS (error: `rds:CreateDBInstance`)
- ElastiCache (error: `elasticache:DescribeReplicationGroups`)
- CloudWatch Logs (error: `logs:FilterLogEvents`)

⚠️ **Blocked**:
- CloudFront (account verification required - contact AWS Support)

## Security Best Practices

1. **Principle of Least Privilege**: Start with minimal permissions, add as needed
2. **Resource-Specific Policies**: Restrict S3 to specific buckets when possible
3. **Condition Keys**: Add conditions for IP restrictions if needed
4. **Regular Audits**: Review and remove unused permissions periodically

## Troubleshooting

### "AccessDenied" Errors

1. **Check Policy Attachment**:
   ```bash
   aws iam list-attached-user-policies --user-name YOUR_USERNAME
   ```

2. **Test Specific Permission**:
   ```bash
   aws apprunner describe-service --service-arn "..." --region us-east-1
   ```

3. **Check Service Control Policies**: If using AWS Organizations, check SCPs

### "Account Verification Required" (CloudFront)

This is not a permissions issue. Contact AWS Support to verify your account for CloudFront.

## Next Steps

1. **Create the IAM Policy** using the JSON above
2. **Attach to your IAM user/role**
3. **Test permissions**:
   ```bash
   aws apprunner describe-service --service-arn "..." --region us-east-1
   aws rds describe-db-instances --region us-east-1
   ```
4. **Run deployment scripts**:
   ```bash
   ./scripts/deploy-apprunner.sh
   ./scripts/setup-rds-postgres.sh
   ```



