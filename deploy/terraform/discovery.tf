resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "techcorp.local"
  description = "Private DNS for TechCorp RAG services"
  vpc         = data.aws_vpc.default.id
  tags        = local.common_tags
}

resource "aws_service_discovery_service" "qdrant" {
  name = "qdrant"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    dns_records {
      ttl  = 10
      type = "A"
    }
    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }

  tags = local.common_tags
}
