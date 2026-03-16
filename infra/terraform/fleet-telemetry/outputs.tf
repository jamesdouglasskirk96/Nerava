output "nlb_dns_name" {
  description = "DNS name of the Network Load Balancer"
  value       = aws_lb.fleet_telemetry.dns_name
}

output "telemetry_fqdn" {
  description = "Fully qualified domain name for Fleet Telemetry"
  value       = local.fqdn
}

output "ecs_service_arn" {
  description = "ARN of the ECS service"
  value       = aws_ecs_service.fleet_telemetry.id
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.fleet_telemetry.name
}
