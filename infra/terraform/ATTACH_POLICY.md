# Attach Custom IAM Policy

Since attaching multiple managed policies exceeds your account quota, use this single custom policy instead.

## Steps to Attach Policy

### Option 1: Using AWS Console

1. Go to IAM Console → Users → `james.douglass.kirk2@gmail.com`
2. Click "Add permissions" → "Create inline policy"
3. Click "JSON" tab
4. Copy the contents of `iam-policy.json`
5. Paste into the JSON editor
6. Click "Review policy"
7. Name it: `NeravaTerraformDeploy`
8. Click "Create policy"

### Option 2: Using AWS CLI

```bash
# Create the policy
aws iam put-user-policy \
  --user-name james.douglass.kirk2@gmail.com \
  --policy-name NeravaTerraformDeploy \
  --policy-document file://infra/terraform/iam-policy.json
```

### Option 3: Using Terraform (if you have permissions)

If you have permission to create IAM policies, you can use this Terraform code:

```hcl
resource "aws_iam_user_policy" "terraform_deploy" {
  name   = "NeravaTerraformDeploy"
  user   = "james.douglass.kirk2@gmail.com"
  policy = file("${path.module}/iam-policy.json")
}
```

## Verify Policy Attachment

```bash
aws iam list-user-policies --user-name james.douglass.kirk2@gmail.com
```

## After Attaching Policy

1. Re-run Terraform:
   ```bash
   cd infra/terraform
   terraform apply
   ```

2. If RDS instance already exists, either:
   - Delete it: `aws rds delete-db-instance --db-instance-identifier nerava-db --skip-final-snapshot`
   - Or change the identifier in `rds.tf` to something else

## Policy Scope

This policy grants only the minimum permissions needed for Terraform to deploy:
- ECS cluster and service management
- Route53 hosted zone and record management
- Secrets Manager operations (including tagging)
- RDS instance management
- EC2 resources (VPC, subnets, security groups, etc.)
- IAM role and policy management
- ECR repository management
- ALB/ELB management
- ACM certificate management
- CloudWatch log group management

It does NOT grant:
- Full administrative access
- Access to other users' resources
- Billing or account management permissions







