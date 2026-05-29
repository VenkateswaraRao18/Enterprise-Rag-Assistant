locals {
  name_prefix = var.project_name

  common_tags = {
    Project = var.project_name
    Managed = "terraform"
  }

  api_image = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
}
