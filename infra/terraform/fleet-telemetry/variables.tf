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

variable "domain_name" {
  description = "Base domain name"
  type        = string
  default     = "nerava.network"
}

variable "telemetry_subdomain" {
  description = "Subdomain for Fleet Telemetry server"
  type        = string
  default     = "telemetry"
}

variable "image_tag" {
  description = "Docker image tag for fleet-telemetry"
  type        = string
  default     = "latest"
}

variable "fleet_telemetry_image" {
  description = "Fleet Telemetry Docker image"
  type        = string
  default     = "tesla/fleet-telemetry"
}

variable "task_cpu" {
  description = "CPU units for Fargate task (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memory in MB for Fargate task"
  type        = number
  default     = 512
}

variable "desired_count" {
  description = "Number of Fargate tasks"
  type        = number
  default     = 1
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

variable "vpc_name" {
  description = "Name tag of the existing VPC to use"
  type        = string
  default     = "nerava-vpc"
}
