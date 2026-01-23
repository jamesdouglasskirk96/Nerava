#!/usr/bin/env python3
"""
Automated AWS deployment script for Nerava.
This script automates the manual setup steps and deploys all infrastructure.
"""

import boto3
import json
import subprocess
import sys
import time
import os
from pathlib import Path

# Configuration
AWS_REGION = "us-east-1"
DOMAIN_NAME = "nerava.network"
PROJECT_NAME = "nerava"
GITHUB_REPO = "jamesdouglasskirk96/Nerava"

# Initialize AWS clients
route53 = boto3.client("route53", region_name=AWS_REGION)
acm = boto3.client("acm", region_name=AWS_REGION)
iam = boto3.client("iam")
secretsmanager = boto3.client("secretsmanager", region_name=AWS_REGION)
ecr = boto3.client("ecr", region_name=AWS_REGION)
ecs = boto3.client("ecs", region_name=AWS_REGION)

def get_account_id():
    """Get AWS account ID"""
    sts = boto3.client("sts")
    return sts.get_caller_identity()["Account"]

def find_or_create_route53_zone():
    """Find existing Route53 hosted zone or create a new one"""
    print("Checking Route53 hosted zone...")
    
    try:
        zones = route53.list_hosted_zones()
        for zone in zones.get("HostedZones", []):
            if zone["Name"] == f"{DOMAIN_NAME}.":
                zone_id = zone["Id"].split("/")[-1]
                print(f"Found existing hosted zone: {zone_id}")
                return zone_id
    except Exception as e:
        print(f"Error checking Route53 zones: {e}")
    
    # Create new hosted zone
    print(f"Creating new Route53 hosted zone for {DOMAIN_NAME}...")
    try:
        response = route53.create_hosted_zone(
            Name=DOMAIN_NAME,
            CallerReference=f"nerava-{int(time.time())}"
        )
        zone_id = response["HostedZone"]["Id"].split("/")[-1]
        print(f"Created hosted zone: {zone_id}")
        print(f"Nameservers: {', '.join(response['DelegationSet']['NameServers'])}")
        print("IMPORTANT: Update your domain registrar with these nameservers!")
        return zone_id
    except Exception as e:
        print(f"Error creating hosted zone: {e}")
        sys.exit(1)

def request_acm_certificate(zone_id):
    """Request ACM certificate for domain"""
    print("Checking for existing ACM certificate...")
    
    try:
        certs = acm.list_certificates()
        for cert in certs.get("CertificateSummaryList", []):
            if cert["DomainName"] == f"*.{DOMAIN_NAME}":
                cert_arn = cert["CertificateArn"]
                # Check if certificate is validated
                cert_detail = acm.describe_certificate(CertificateArn=cert_arn)
                if cert_detail["Certificate"]["Status"] == "ISSUED":
                    print(f"Found validated certificate: {cert_arn}")
                    return cert_arn
                else:
                    print(f"Found certificate but not yet validated: {cert_arn}")
                    print("Waiting for validation...")
                    return wait_for_certificate_validation(cert_arn, zone_id)
    except Exception as e:
        print(f"Error checking certificates: {e}")
    
    # Request new certificate
    print(f"Requesting ACM certificate for *.{DOMAIN_NAME} and {DOMAIN_NAME}...")
    try:
        response = acm.request_certificate(
            DomainName=f"*.{DOMAIN_NAME}",
            SubjectAlternativeNames=[DOMAIN_NAME],
            ValidationMethod="DNS",
            DomainValidationOptions=[
                {
                    "DomainName": f"*.{DOMAIN_NAME}",
                    "ValidationDomain": DOMAIN_NAME
                },
                {
                    "DomainName": DOMAIN_NAME,
                    "ValidationDomain": DOMAIN_NAME
                }
            ]
        )
        cert_arn = response["CertificateArn"]
        print(f"Certificate requested: {cert_arn}")
        
        # Wait for validation records
        return wait_for_certificate_validation(cert_arn, zone_id)
    except Exception as e:
        print(f"Error requesting certificate: {e}")
        sys.exit(1)

def wait_for_certificate_validation(cert_arn, zone_id):
    """Wait for certificate validation and create DNS records"""
    print("Waiting for certificate validation details...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            cert_detail = acm.describe_certificate(CertificateArn=cert_arn)
            cert = cert_detail["Certificate"]
            
            if cert["Status"] == "ISSUED":
                print("Certificate is validated!")
                return cert_arn
            
            # Check for validation records
            validation_options = cert.get("DomainValidationOptions", [])
            if validation_options:
                for option in validation_options:
                    resource_record = option.get("ResourceRecord")
                    if resource_record:
                        # Create CNAME record in Route53
                        try:
                            route53.change_resource_record_sets(
                                HostedZoneId=zone_id,
                                ChangeBatch={
                                    "Changes": [{
                                        "Action": "UPSERT",
                                        "ResourceRecordSet": {
                                            "Name": resource_record["Name"],
                                            "Type": resource_record["Type"],
                                            "TTL": 300,
                                            "ResourceRecords": [{
                                                "Value": resource_record["Value"]
                                            }]
                                        }
                                    }]
                                }
                            )
                            print(f"Created validation record: {resource_record['Name']}")
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                print(f"Error creating validation record: {e}")
            
            print(f"Waiting for validation... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(10)
        except Exception as e:
            print(f"Error checking certificate status: {e}")
            time.sleep(10)
    
    print("WARNING: Certificate validation is taking longer than expected.")
    print("You may need to manually add DNS validation records.")
    return cert_arn

def setup_github_oidc():
    """Setup GitHub OIDC provider"""
    print("Checking for GitHub OIDC provider...")
    
    provider_url = "https://token.actions.githubusercontent.com"
    
    try:
        providers = iam.list_open_id_connect_providers()
        for provider_arn in providers.get("OpenIDConnectProviderList", []):
            provider = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
            if provider["Url"] == provider_url:
                print(f"Found existing OIDC provider: {provider_arn}")
                return provider_arn
    except Exception as e:
        print(f"Error checking OIDC providers: {e}")
    
    # Create OIDC provider
    print("Creating GitHub OIDC provider...")
    try:
        account_id = get_account_id()
        response = iam.create_open_id_connect_provider(
            Url=provider_url,
            ClientIDList=["sts.amazonaws.com"],
            ThumbprintList=[
                "6938fd4d98bab03faadb97b34396831e3780aea1",  # GitHub's thumbprint
                "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
            ]
        )
        provider_arn = response["OpenIDConnectProviderArn"]
        print(f"Created OIDC provider: {provider_arn}")
        return provider_arn
    except Exception as e:
        if "EntityAlreadyExists" in str(e):
            # Provider exists, get its ARN
            providers = iam.list_open_id_connect_providers()
            for provider_arn in providers.get("OpenIDConnectProviderList", []):
                provider = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
                if provider["Url"] == provider_url:
                    return provider_arn
        print(f"Error creating OIDC provider: {e}")
        return ""

def create_terraform_tfvars(zone_id, cert_arn, oidc_arn):
    """Create terraform.tfvars file"""
    print("Creating terraform.tfvars...")
    
    tfvars_path = Path("infra/terraform/terraform.tfvars")
    tfvars_path.parent.mkdir(parents=True, exist_ok=True)
    
    tfvars_content = f"""# AWS Configuration
aws_region = "{AWS_REGION}"

# Project Configuration
project_name = "{PROJECT_NAME}"
environment  = "prod"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# Domain Configuration
domain_name = "{DOMAIN_NAME}"

# ACM Certificate ARN
acm_certificate_arn = "{cert_arn}"

# Route53 Configuration
route53_zone_id = "{zone_id}"

# RDS Configuration
rds_instance_class         = "db.t3.micro"
rds_allocated_storage      = 20
rds_backup_retention_period = 7

# ECS Task Configuration
ecs_task_cpu = {{
  backend  = 512
  driver   = 256
  merchant = 256
  admin    = 256
  landing  = 512
}}

ecs_task_memory = {{
  backend  = 1024
  driver   = 512
  merchant = 512
  admin    = 512
  landing  = 1024
}}

ecs_desired_count = {{
  backend  = 1
  driver   = 1
  merchant = 1
  admin    = 1
  landing  = 1
}}

# GitHub OIDC Configuration
github_repository        = "{GITHUB_REPO}"
github_oidc_provider_arn = "{oidc_arn}"
"""
    
    with open(tfvars_path, "w") as f:
        f.write(tfvars_content)
    
    print(f"Created {tfvars_path}")

def run_terraform_init():
    """Run terraform init"""
    print("Running terraform init...")
    try:
        subprocess.run(
            ["terraform", "init"],
            cwd="infra/terraform",
            check=True
        )
        print("Terraform initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running terraform init: {e}")
        sys.exit(1)

def run_terraform_apply():
    """Run terraform apply"""
    print("Running terraform apply...")
    print("This will create all AWS resources. This may take 10-15 minutes...")
    try:
        subprocess.run(
            ["terraform", "apply", "-auto-approve"],
            cwd="infra/terraform",
            check=True
        )
        print("Terraform apply completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error running terraform apply: {e}")
        sys.exit(1)

def main():
    """Main deployment function"""
    print("=" * 60)
    print("Nerava AWS Deployment Script")
    print("=" * 60)
    print()
    
    # Step 1: Route53
    zone_id = find_or_create_route53_zone()
    print()
    
    # Step 2: ACM Certificate
    cert_arn = request_acm_certificate(zone_id)
    print()
    
    # Step 3: GitHub OIDC
    oidc_arn = setup_github_oidc()
    print()
    
    # Step 4: Create terraform.tfvars
    create_terraform_tfvars(zone_id, cert_arn, oidc_arn)
    print()
    
    # Step 5: Terraform init
    run_terraform_init()
    print()
    
    # Step 6: Terraform apply
    print("Ready to deploy infrastructure. Continue? (y/n): ", end="")
    response = input().strip().lower()
    if response != "y":
        print("Deployment cancelled.")
        sys.exit(0)
    
    run_terraform_apply()
    print()
    
    print("=" * 60)
    print("Infrastructure deployment complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Populate secrets in AWS Secrets Manager (see MANUAL_SETUP.md)")
    print("2. Build and push Docker images to ECR")
    print("3. Run database migrations")
    print("4. Verify deployment with smoke tests")

if __name__ == "__main__":
    main()




