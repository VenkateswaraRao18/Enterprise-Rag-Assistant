#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TF_DIR="$ROOT/deploy/terraform"
TF="${TF:-$ROOT/deploy/tools/terraform}"
REGION="${AWS_REGION:-us-east-1}"

cd "$TF_DIR"
# Use CloudFront as API base so the browser stays on HTTPS (no mixed-content block).
API_URL="$("$TF" output -raw cloudfront_url)"
BUCKET="$("$TF" output -raw frontend_bucket)"
CF_ID="$("$TF" output -raw cloudfront_distribution_id)"
CF_URL="$("$TF" output -raw cloudfront_url)"

# Optional API_KEY from .env for frontend build
API_KEY=""
if [[ -f "$ROOT/.env" ]]; then
  API_KEY="$(grep -E '^API_KEY=' "$ROOT/.env" | cut -d= -f2- | tr -d '"' | tr -d "'" || true)"
fi

echo "==> Building frontend (API=$API_URL)"
cd "$ROOT/frontend"
export VITE_API_BASE_URL="$API_URL"
export VITE_API_KEY="$API_KEY"
npm ci
npm run build

echo "==> Sync to s3://$BUCKET"
aws s3 sync dist/ "s3://$BUCKET/" --delete --region "$REGION"

echo "==> CloudFront invalidation"
aws cloudfront create-invalidation --distribution-id "$CF_ID" --paths "/*" >/dev/null

echo ""
echo "Frontend URL: $CF_URL"
echo "Update API CORS if needed:"
echo "  terraform apply -var='cors_origins=http://localhost:5173,$CF_URL'"
