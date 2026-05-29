#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TF_DIR="$ROOT/deploy/terraform"
TF="${TF:-$ROOT/deploy/tools/terraform}"
REGION="${AWS_REGION:-us-east-1}"
TAG="${IMAGE_TAG:-latest}"

cd "$TF_DIR"
REPO_URL="$("$TF" output -raw ecr_api_repository_url 2>/dev/null || true)"

if [[ -z "$REPO_URL" ]]; then
  echo "ECR repo not found. Run: cd deploy/terraform && terraform apply -target=aws_ecr_repository.api"
  exit 1
fi

ACCOUNT="$(echo "$REPO_URL" | cut -d. -f1)"
echo "==> Logging in to ECR ($ACCOUNT) in $REGION"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"

echo "==> Building API image (linux/amd64 for AWS Fargate)"
$DOCKER buildx build --platform linux/amd64 -t techcorp-rag-api:"$TAG" "$ROOT" --load

echo "==> Pushing $REPO_URL:$TAG"
docker tag techcorp-rag-api:"$TAG" "$REPO_URL:$TAG"
docker push "$REPO_URL:$TAG"

echo "Done. Image: $REPO_URL:$TAG"
