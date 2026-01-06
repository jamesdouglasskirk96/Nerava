variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "nerava"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "domain_name" {
  description = "Base domain name (e.g., nerava.network)"
  type        = string
  default     = "nerava.network"
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for HTTPS (must cover *.nerava.network and nerava.network)"
  type        = string
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "rds_backup_retention_period" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 7
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS tasks (1024 = 1 vCPU)"
  type        = map(number)
  default = {
    backend  = 512
    driver   = 256
    merchant = 256
    admin    = 256
    landing  = 512
  }
}

variable "ecs_task_memory" {
  description = "Memory for ECS tasks in MB"
  type        = map(number)
  default = {
    backend  = 1024
    driver   = 512
    merchant = 512
    admin    = 512
    landing  = 1024
  }
}

variable "ecs_desired_count" {
  description = "Desired number of tasks per service"
  type        = map(number)
  default = {
    backend  = 1
    driver   = 1
    merchant = 1
    admin    = 1
    landing  = 1
  }
}

variable "github_repository" {
  description = "GitHub repository in format owner/repo"
  type        = string
  default     = ""
}

variable "github_oidc_provider_arn" {
  description = "ARN of GitHub OIDC provider (if using OIDC)"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for domain"
  type        = string
  default     = ""
}

