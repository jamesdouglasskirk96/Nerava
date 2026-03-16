# ECS Fargate task and service for Fleet Telemetry

resource "aws_ecs_task_definition" "fleet_telemetry" {
  family                   = local.name_prefix
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "fleet-telemetry"
    image     = "${var.fleet_telemetry_image}:${var.image_tag}"
    essential = true

    portMappings = [{
      containerPort = 443
      protocol      = "tcp"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.fleet_telemetry.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "fleet-telemetry"
      }
    }

    # Config and TLS certs are mounted from Secrets Manager
    # The fleet-telemetry binary reads config from /etc/fleet-telemetry/config.json
    secrets = [
      {
        name      = "FLEET_TELEMETRY_CONFIG"
        valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/fleet-telemetry/config"
      },
    ]

    environment = [
      {
        name  = "FLEET_TELEMETRY_PORT"
        value = "443"
      },
    ]
  }])

  tags = {
    Name        = local.name_prefix
    Project     = var.project_name
    Environment = var.environment
  }
}

data "aws_caller_identity" "current" {}

resource "aws_ecs_service" "fleet_telemetry" {
  name            = local.name_prefix
  cluster         = data.aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.fleet_telemetry.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.fleet_telemetry.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.fleet_telemetry.arn
    container_name   = "fleet-telemetry"
    container_port   = 443
  }

  depends_on = [aws_lb_listener.fleet_telemetry]

  tags = {
    Name        = local.name_prefix
    Project     = var.project_name
    Environment = var.environment
  }
}
