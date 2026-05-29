variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "techcorp-rag"
}

variable "api_image_tag" {
  description = "Docker tag pushed to ECR (run deploy/scripts/01-push-api-image.sh first)"
  type        = string
  default     = "latest"
}

variable "cors_origins" {
  description = "Comma-separated origins for FastAPI CORS (add CloudFront URL after frontend deploy)"
  type        = string
  default     = "http://localhost:5173,http://127.0.0.1:5173"
}

variable "api_cpu" {
  type    = number
  default = 512
}

variable "api_memory" {
  type    = number
  default = 1024
}

variable "qdrant_cpu" {
  type    = number
  default = 256
}

variable "qdrant_memory" {
  type    = number
  default = 512
}
