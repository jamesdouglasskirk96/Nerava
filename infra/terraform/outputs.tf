output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
}

output "rds_address" {
  description = "RDS instance address"
  value       = aws_db_instance.main.address
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value = {
    backend  = aws_ecr_repository.backend.repository_url
    driver   = aws_ecr_repository.driver.repository_url
    merchant = aws_ecr_repository.merchant.repository_url
    admin    = aws_ecr_repository.admin.repository_url
    landing  = aws_ecr_repository.landing.repository_url
  }
}

output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.route53_zone_id != "" ? var.route53_zone_id : aws_route53_zone.main[0].id
}

output "backend_secrets_arn" {
  description = "Backend secrets ARN"
  value       = aws_secretsmanager_secret.backend_database.arn
  sensitive   = true
}

