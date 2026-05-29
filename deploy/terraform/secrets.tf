resource "aws_secretsmanager_secret" "app" {
  name        = "${local.name_prefix}/prod"
  description = "Gemini API key and optional API_KEY for TechCorp RAG"
  tags        = local.common_tags
}

# Placeholder version — overwrite with deploy/scripts/02-put-secrets.sh
resource "aws_secretsmanager_secret_version" "app_placeholder" {
  secret_string = jsonencode({
    GEMINI_API_KEY = "REPLACE_ME"
    API_KEY        = ""
  })
  secret_id = aws_secretsmanager_secret.app.id

  lifecycle {
    ignore_changes = [secret_string]
  }
}
