# CloudWatch log group for Fleet Telemetry

resource "aws_cloudwatch_log_group" "fleet_telemetry" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${local.name_prefix}-logs"
    Project     = var.project_name
    Environment = var.environment
  }
}
