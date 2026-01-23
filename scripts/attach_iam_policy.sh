#!/bin/bash
# Script to attach the custom IAM policy for Terraform deployment

set -e

USER_NAME="james.douglass.kirk2@gmail.com"
POLICY_NAME="NeravaTerraformDeploy"
POLICY_FILE="infra/terraform/iam-policy.json"

echo "Attaching IAM policy to user: $USER_NAME"
echo "Policy name: $POLICY_NAME"
echo ""

# Check if policy file exists
if [ ! -f "$POLICY_FILE" ]; then
    echo "Error: Policy file not found: $POLICY_FILE"
    exit 1
fi

# Attach the policy
echo "Creating/updating inline policy..."
aws iam put-user-policy \
    --user-name "$USER_NAME" \
    --policy-name "$POLICY_NAME" \
    --policy-document "file://$POLICY_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Policy attached successfully!"
    echo ""
    echo "You can now run:"
    echo "  cd infra/terraform"
    echo "  terraform apply"
else
    echo ""
    echo "❌ Failed to attach policy. Check your AWS credentials and permissions."
    exit 1
fi




