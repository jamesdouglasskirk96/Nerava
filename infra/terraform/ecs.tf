# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# Backend Task Definition
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu["backend"]
  memory                   = var.ecs_task_memory["backend"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:latest"

    portMappings = [{
      containerPort = 8001
      protocol      = "tcp"
    }]

    environment = [
      { name = "ENV", value = "prod" },
      { name = "ALLOWED_ORIGINS", value = "https://app.nerava.network,https://www.nerava.network,https://merchant.nerava.network,https://admin.nerava.network" },
      { name = "ALLOWED_HOSTS", value = "api.nerava.network,*.nerava.network" },
      { name = "PUBLIC_BASE_URL", value = "https://api.nerava.network" },
      { name = "FRONTEND_URL", value = "https://app.nerava.network" },
      { name = "DEMO_MODE", value = "false" },
      { name = "MERCHANT_AUTH_MOCK", value = "false" },
      { name = "OTP_PROVIDER", value = "twilio_verify" }
    ]

    secrets = [
      {
        name      = "DATABASE_URL"
        valueFrom = aws_secretsmanager_secret.backend_database.arn
      },
      {
        name      = "JWT_SECRET"
        valueFrom = aws_secretsmanager_secret.backend_jwt_secret.arn
      },
      {
        name      = "TOKEN_ENCRYPTION_KEY"
        valueFrom = aws_secretsmanager_secret.backend_token_encryption_key.arn
      },
      {
        name      = "TWILIO_ACCOUNT_SID"
        valueFrom = "${aws_secretsmanager_secret.backend_twilio.arn}:account_sid::"
      },
      {
        name      = "TWILIO_AUTH_TOKEN"
        valueFrom = "${aws_secretsmanager_secret.backend_twilio.arn}:auth_token::"
      },
      {
        name      = "TWILIO_VERIFY_SERVICE_SID"
        valueFrom = "${aws_secretsmanager_secret.backend_twilio.arn}:verify_service_sid::"
      },
      {
        name      = "GOOGLE_OAUTH_CLIENT_ID"
        valueFrom = "${aws_secretsmanager_secret.backend_google.arn}:oauth_client_id::"
      },
      {
        name      = "GOOGLE_OAUTH_CLIENT_SECRET"
        valueFrom = "${aws_secretsmanager_secret.backend_google.arn}:oauth_client_secret::"
      },
      {
        name      = "GOOGLE_PLACES_API_KEY"
        valueFrom = "${aws_secretsmanager_secret.backend_google.arn}:places_api_key::"
      },
      {
        name      = "SQUARE_APPLICATION_ID_PRODUCTION"
        valueFrom = "${aws_secretsmanager_secret.backend_square.arn}:application_id::"
      },
      {
        name      = "SQUARE_APPLICATION_SECRET_PRODUCTION"
        valueFrom = "${aws_secretsmanager_secret.backend_square.arn}:application_secret::"
      },
      {
        name      = "SQUARE_WEBHOOK_SIGNATURE_KEY"
        valueFrom = "${aws_secretsmanager_secret.backend_square.arn}:webhook_signature_key::"
      },
      {
        name      = "STRIPE_SECRET_KEY"
        valueFrom = "${aws_secretsmanager_secret.backend_stripe.arn}:secret_key::"
      },
      {
        name      = "STRIPE_WEBHOOK_SECRET"
        valueFrom = "${aws_secretsmanager_secret.backend_stripe.arn}:webhook_secret::"
      },
      {
        name      = "STRIPE_CONNECT_CLIENT_ID"
        valueFrom = "${aws_secretsmanager_secret.backend_stripe.arn}:connect_client_id::"
      },
      {
        name      = "SMARTCAR_CLIENT_ID"
        valueFrom = "${aws_secretsmanager_secret.backend_smartcar.arn}:client_id::"
      },
      {
        name      = "SMARTCAR_CLIENT_SECRET"
        valueFrom = "${aws_secretsmanager_secret.backend_smartcar.arn}:client_secret::"
      },
      {
        name      = "SMARTCAR_STATE_SECRET"
        valueFrom = "${aws_secretsmanager_secret.backend_smartcar.arn}:state_secret::"
      },
      {
        name      = "POSTHOG_KEY"
        valueFrom = aws_secretsmanager_secret.backend_posthog.arn
      },
      {
        name      = "TESLA_CLIENT_ID"
        valueFrom = "${data.aws_secretsmanager_secret.backend_tesla.arn}:client_id::"
      },
      {
        name      = "TESLA_CLIENT_SECRET"
        valueFrom = "${data.aws_secretsmanager_secret.backend_tesla.arn}:client_secret::"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:8001/health')\""]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

# Driver Task Definition
resource "aws_ecs_task_definition" "driver" {
  family                   = "${var.project_name}-driver"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu["driver"]
  memory                   = var.ecs_task_memory["driver"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name  = "driver"
    image = "${aws_ecr_repository.driver.repository_url}:latest"

    portMappings = [{
      containerPort = 3001
      protocol      = "tcp"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.driver.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:3001/ || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 30
    }
  }])
}

# Merchant Task Definition
resource "aws_ecs_task_definition" "merchant" {
  family                   = "${var.project_name}-merchant"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu["merchant"]
  memory                   = var.ecs_task_memory["merchant"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name  = "merchant"
    image = "${aws_ecr_repository.merchant.repository_url}:latest"

    portMappings = [{
      containerPort = 3002
      protocol      = "tcp"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.merchant.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:3002/ || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 30
    }
  }])
}

# Admin Task Definition
resource "aws_ecs_task_definition" "admin" {
  family                   = "${var.project_name}-admin"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu["admin"]
  memory                   = var.ecs_task_memory["admin"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name  = "admin"
    image = "${aws_ecr_repository.admin.repository_url}:latest"

    portMappings = [{
      containerPort = 3003
      protocol      = "tcp"
    }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.admin.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:3003/ || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 30
    }
  }])
}

# Landing Task Definition
resource "aws_ecs_task_definition" "landing" {
  family                   = "${var.project_name}-landing"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu["landing"]
  memory                   = var.ecs_task_memory["landing"]
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name  = "landing"
    image = "${aws_ecr_repository.landing.repository_url}:latest"

    portMappings = [{
      containerPort = 3000
      protocol      = "tcp"
    }]

    environment = [
      { name = "NEXT_PUBLIC_DRIVER_APP_URL", value = "https://app.nerava.network" },
      { name = "NEXT_PUBLIC_MERCHANT_APP_URL", value = "https://merchant.nerava.network" },
      { name = "NEXT_PUBLIC_CHARGER_PORTAL_URL", value = "https://charger.nerava.network" }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.landing.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

# ECS Services
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.ecs_desired_count["backend"]
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8001
  }

  depends_on = [aws_lb_listener.https]

  tags = {
    Name = "${var.project_name}-backend-service"
  }
}

resource "aws_ecs_service" "driver" {
  name            = "${var.project_name}-driver"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.driver.arn
  desired_count   = var.ecs_desired_count["driver"]
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.driver.arn
    container_name   = "driver"
    container_port   = 3001
  }

  depends_on = [aws_lb_listener.https]

  tags = {
    Name = "${var.project_name}-driver-service"
  }
}

resource "aws_ecs_service" "merchant" {
  name            = "${var.project_name}-merchant"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.merchant.arn
  desired_count   = var.ecs_desired_count["merchant"]
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.merchant.arn
    container_name   = "merchant"
    container_port   = 3002
  }

  depends_on = [aws_lb_listener.https]

  tags = {
    Name = "${var.project_name}-merchant-service"
  }
}

resource "aws_ecs_service" "admin" {
  name            = "${var.project_name}-admin"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.admin.arn
  desired_count   = var.ecs_desired_count["admin"]
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.admin.arn
    container_name   = "admin"
    container_port   = 3003
  }

  depends_on = [aws_lb_listener.https]

  tags = {
    Name = "${var.project_name}-admin-service"
  }
}

resource "aws_ecs_service" "landing" {
  name            = "${var.project_name}-landing"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.landing.arn
  desired_count   = var.ecs_desired_count["landing"]
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.landing.arn
    container_name   = "landing"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.https]

  tags = {
    Name = "${var.project_name}-landing-service"
  }
}

