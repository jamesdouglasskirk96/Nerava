# Database Secret
resource "aws_secretsmanager_secret" "backend_database" {
  name        = "${var.project_name}/backend/database"
  description = "RDS PostgreSQL connection string and credentials"

  tags = {
    Name = "${var.project_name}-backend-database-secret"
  }
}

# Note: DATABASE_URL will be updated after RDS is created via a null_resource or manually
# The initial value is a placeholder that will be replaced
resource "aws_secretsmanager_secret_version" "backend_database" {
  secret_id = aws_secretsmanager_secret.backend_database.id
  secret_string = "postgresql://nerava_admin:${random_password.db_password.result}@PLACEHOLDER_RDS_ENDPOINT:5432/nerava"
  
  depends_on = [random_password.db_password]
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Update DATABASE_URL after RDS is created
resource "null_resource" "update_database_secret" {
  triggers = {
    rds_endpoint = aws_db_instance.main.address
    password     = random_password.db_password.result
  }
  
  provisioner "local-exec" {
    command = <<-EOT
      aws secretsmanager update-secret \
        --secret-id ${aws_secretsmanager_secret.backend_database.arn} \
        --secret-string "postgresql://nerava_admin:${random_password.db_password.result}@${aws_db_instance.main.address}:5432/nerava" \
        --region ${var.aws_region}
    EOT
  }
  
  depends_on = [aws_db_instance.main, aws_secretsmanager_secret_version.backend_database]
}

# JWT Secret
resource "aws_secretsmanager_secret" "backend_jwt_secret" {
  name        = "${var.project_name}/backend/jwt-secret"
  description = "JWT secret for token signing"

  tags = {
    Name = "${var.project_name}-backend-jwt-secret"
  }
}

resource "aws_secretsmanager_secret_version" "backend_jwt_secret" {
  secret_id     = aws_secretsmanager_secret.backend_jwt_secret.id
  secret_string = "CHANGE_ME_GENERATE_WITH_PYTHON_SECRETS_TOKEN_URLSAFE"
}

# Token Encryption Key
resource "aws_secretsmanager_secret" "backend_token_encryption_key" {
  name        = "${var.project_name}/backend/token-encryption-key"
  description = "Fernet key for token encryption"

  tags = {
    Name = "${var.project_name}-backend-token-encryption-key"
  }
}

resource "aws_secretsmanager_secret_version" "backend_token_encryption_key" {
  secret_id     = aws_secretsmanager_secret.backend_token_encryption_key.id
  secret_string = "CHANGE_ME_GENERATE_WITH_CRYPTOGRAPHY_FERNET_GENERATE_KEY"
}

# Twilio Credentials
resource "aws_secretsmanager_secret" "backend_twilio" {
  name        = "${var.project_name}/backend/twilio"
  description = "Twilio API credentials"

  tags = {
    Name = "${var.project_name}-backend-twilio-secret"
  }
}

resource "aws_secretsmanager_secret_version" "backend_twilio" {
  secret_id = aws_secretsmanager_secret.backend_twilio.id
  secret_string = jsonencode({
    account_sid        = "CHANGE_ME"
    auth_token         = "CHANGE_ME"
    verify_service_sid = "CHANGE_ME"
    from_number        = "" # Optional, only if using twilio_sms
  })
}

# Google OAuth Credentials
resource "aws_secretsmanager_secret" "backend_google" {
  name        = "${var.project_name}/backend/google"
  description = "Google OAuth credentials"

  tags = {
    Name = "${var.project_name}-backend-google-secret"
  }
}

resource "aws_secretsmanager_secret_version" "backend_google" {
  secret_id = aws_secretsmanager_secret.backend_google.id
  secret_string = jsonencode({
    client_id     = "CHANGE_ME"
    oauth_client_id     = "CHANGE_ME"
    oauth_client_secret = "CHANGE_ME"
    redirect_uri  = "https://api.nerava.network/v1/merchants/google/callback"
    places_api_key = "CHANGE_ME"
  })
}

# Square API Credentials
resource "aws_secretsmanager_secret" "backend_square" {
  name        = "${var.project_name}/backend/square"
  description = "Square API credentials"

  tags = {
    Name = "${var.project_name}-backend-square-secret"
  }
}

resource "aws_secretsmanager_secret_version" "backend_square" {
  secret_id = aws_secretsmanager_secret.backend_square.id
  secret_string = jsonencode({
    env                    = "production"
    application_id         = "CHANGE_ME"
    application_secret     = "CHANGE_ME"
    redirect_url           = "https://api.nerava.network/v1/merchants/square/callback"
    webhook_signature_key   = "CHANGE_ME"
  })
}

# Stripe Credentials
resource "aws_secretsmanager_secret" "backend_stripe" {
  name        = "${var.project_name}/backend/stripe"
  description = "Stripe API credentials"

  tags = {
    Name = "${var.project_name}-backend-stripe-secret"
  }
}

resource "aws_secretsmanager_secret_version" "backend_stripe" {
  secret_id = aws_secretsmanager_secret.backend_stripe.id
  secret_string = jsonencode({
    secret_key         = "CHANGE_ME"
    webhook_secret     = "CHANGE_ME"
    connect_client_id  = "CHANGE_ME"
  })
}

# Smartcar Credentials
resource "aws_secretsmanager_secret" "backend_smartcar" {
  name        = "${var.project_name}/backend/smartcar"
  description = "Smartcar API credentials"

  tags = {
    Name = "${var.project_name}-backend-smartcar-secret"
  }
}

resource "aws_secretsmanager_secret_version" "backend_smartcar" {
  secret_id = aws_secretsmanager_secret.backend_smartcar.id
  secret_string = jsonencode({
    client_id     = "CHANGE_ME"
    client_secret = "CHANGE_ME"
    redirect_uri  = "https://api.nerava.network/oauth/smartcar/callback"
    mode          = "live"
    state_secret  = "CHANGE_ME_GENERATE_SECURE_RANDOM"
  })
}

# PostHog Key (optional)
resource "aws_secretsmanager_secret" "backend_posthog" {
  name        = "${var.project_name}/backend/posthog"
  description = "PostHog analytics key"

  tags = {
    Name = "${var.project_name}-backend-posthog-secret"
  }
}

resource "aws_secretsmanager_secret_version" "backend_posthog" {
  secret_id     = aws_secretsmanager_secret.backend_posthog.id
  secret_string = "CHANGE_ME_OR_LEAVE_EMPTY_IF_NOT_USED"
}

