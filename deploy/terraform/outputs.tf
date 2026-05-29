output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "ecr_api_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "alb_dns_name" {
  value = aws_lb.api.dns_name
}

output "api_url" {
  value = "http://${aws_lb.api.dns_name}"
}

output "secrets_manager_secret_name" {
  value = aws_secretsmanager_secret.app.name
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "index_task_definition" {
  value = aws_ecs_task_definition.index.family
}

output "qdrant_dns" {
  value = "http://qdrant.techcorp.local:6333"
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.id
}

output "cloudfront_url" {
  value = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "app_url" {
  description = "Public HTTPS app (UI + API via CloudFront)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}

output "private_subnet_ids" {
  value = [for s in data.aws_subnet.selected : s.id]
}

output "api_security_group_id" {
  value = aws_security_group.api.id
}
