# Handle Existing RDS Instance

The Terraform deployment failed because an RDS instance named `nerava-db` already exists.

## Option 1: Delete Existing Instance (Recommended for Fresh Deployment)

```bash
# Delete the existing RDS instance
aws rds delete-db-instance \
  --db-instance-identifier nerava-db \
  --skip-final-snapshot

# Wait for deletion to complete (can take 5-10 minutes)
aws rds wait db-instance-deleted --db-instance-identifier nerava-db
```

Then re-run Terraform:
```bash
cd infra/terraform
terraform apply
```

## Option 2: Use Existing Instance (Import into Terraform)

If you want to keep the existing RDS instance and manage it with Terraform:

```bash
cd infra/terraform

# Import the existing instance
terraform import aws_db_instance.main nerava-db

# Then run apply to sync any differences
terraform apply
```

**Note**: You'll need to ensure the existing instance matches your Terraform configuration, or Terraform will try to modify it.

## Option 3: Change Terraform Identifier

Modify `rds.tf` to use a different identifier:

```hcl
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-db-new"  # Changed from "${var.project_name}-db"
  # ... rest of config
}
```

Then run `terraform apply` again.

## Option 4: Check if Instance is Already Managed

If the RDS instance was created by a previous Terraform run:

```bash
cd infra/terraform
terraform state list | grep rds
```

If it's in the state, you may just need to refresh:
```bash
terraform refresh
terraform apply
```




