# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-backend"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-backend-logs"
  }
}

resource "aws_cloudwatch_log_group" "driver" {
  name              = "/ecs/${var.project_name}-driver"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-driver-logs"
  }
}

resource "aws_cloudwatch_log_group" "merchant" {
  name              = "/ecs/${var.project_name}-merchant"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-merchant-logs"
  }
}

resource "aws_cloudwatch_log_group" "admin" {
  name              = "/ecs/${var.project_name}-admin"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-admin-logs"
  }
}

resource "aws_cloudwatch_log_group" "landing" {
  name              = "/ecs/${var.project_name}-landing"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-landing-logs"
  }
}

