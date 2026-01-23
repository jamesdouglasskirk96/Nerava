# GitHub OIDC Provider (create if not provided and github_repository is set)
resource "aws_iam_openid_connect_provider" "github" {
  count = var.github_oidc_provider_arn == "" && var.github_repository != "" ? 1 : 0

  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1", # GitHub's thumbprint
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"  # Backup thumbprint
  ]

  tags = {
    Name = "${var.project_name}-github-oidc"
  }
}

# Local value for OIDC provider ARN (used in outputs)
locals {
  github_oidc_provider_arn = var.github_oidc_provider_arn != "" ? var.github_oidc_provider_arn : (
    var.github_repository != "" && length(aws_iam_openid_connect_provider.github) > 0 ? aws_iam_openid_connect_provider.github[0].arn : ""
  )
}

