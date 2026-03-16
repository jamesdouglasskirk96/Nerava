# Network Load Balancer for Fleet Telemetry
# NLB in TCP passthrough mode — Fleet Telemetry handles TLS internally

resource "aws_lb" "fleet_telemetry" {
  name               = "${local.name_prefix}-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = data.aws_subnets.public.ids

  enable_deletion_protection = false

  tags = {
    Name        = "${local.name_prefix}-nlb"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "fleet_telemetry" {
  name        = "${local.name_prefix}-tg"
  port        = 443
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    protocol            = "TCP"
    port                = "443"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    interval            = 30
  }

  tags = {
    Name = "${local.name_prefix}-tg"
  }
}

resource "aws_lb_listener" "fleet_telemetry" {
  load_balancer_arn = aws_lb.fleet_telemetry.arn
  port              = 443
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.fleet_telemetry.arn
  }
}
