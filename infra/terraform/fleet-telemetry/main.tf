terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Look up existing VPC
data "aws_vpc" "main" {
  tags = {
    Name = var.vpc_name
  }
}

# Look up public subnets by name pattern (for NLB)
data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["*public*"]
  }
}

# Look up private subnets by name pattern (for ECS tasks)
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }

  filter {
    name   = "tag:Name"
    values = ["*private*"]
  }
}

# Look up existing ECS cluster
data "aws_ecs_cluster" "main" {
  cluster_name = "${var.project_name}-cluster"
}

# Route53 hosted zone
data "aws_route53_zone" "main" {
  name = "${var.domain_name}."
}

locals {
  name_prefix = "${var.project_name}-fleet-telemetry"
  fqdn        = "${var.telemetry_subdomain}.${var.domain_name}"
}
