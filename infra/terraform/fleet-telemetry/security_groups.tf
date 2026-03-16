# Security group for Fleet Telemetry ECS tasks

resource "aws_security_group" "fleet_telemetry" {
  name        = "${local.name_prefix}-sg"
  description = "Allow inbound TLS from NLB for Fleet Telemetry"
  vpc_id      = data.aws_vpc.main.id

  # Ingress from NLB (TCP 443)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "TLS from Tesla vehicles via NLB"
  }

  # Egress — allow all (for HTTP dispatch to api.nerava.network)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name        = "${local.name_prefix}-sg"
    Project     = var.project_name
    Environment = var.environment
  }
}
