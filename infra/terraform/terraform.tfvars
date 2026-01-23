# AWS Configuration
aws_region = "us-east-1"

# Project Configuration
project_name = "nerava"
environment  = "prod"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# Domain Configuration
domain_name = "nerava.network"

# ACM Certificate ARN (leave empty to create automatically)
acm_certificate_arn = ""

# Route53 Configuration (leave empty to create automatically)
route53_zone_id = ""

# RDS Configuration
rds_instance_class         = "db.t3.micro"
rds_allocated_storage      = 20
rds_backup_retention_period = 7

# ECS Task Configuration
ecs_task_cpu = {
  backend  = 512
  driver   = 256
  merchant = 256
  admin    = 256
  landing  = 512
}

ecs_task_memory = {
  backend  = 1024
  driver   = 512
  merchant = 512
  admin    = 512
  landing  = 1024
}

ecs_desired_count = {
  backend  = 1
  driver   = 1
  merchant = 1
  admin    = 1
  landing  = 1
}

# GitHub OIDC Configuration
github_repository        = "jamesdouglasskirk96/Nerava"
github_oidc_provider_arn = ""




