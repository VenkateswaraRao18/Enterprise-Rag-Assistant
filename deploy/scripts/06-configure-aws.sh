#!/usr/bin/env bash
# Configure AWS CLI for Path B (us-east-1).
# Do NOT commit credentials to git.
set -euo pipefail

export PATH="${HOME}/Library/Python/3.9/bin:${PATH:-}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-default}"
AWS_DIR="${HOME}/.aws"

mkdir -p "$AWS_DIR"
chmod 700 "$AWS_DIR"

if [[ -n "${AWS_ACCESS_KEY_ID:-}" && -n "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
  echo "==> Writing profile [$PROFILE] from environment variables"
  aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID" --profile "$PROFILE"
  aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY" --profile "$PROFILE"
  aws configure set region "$REGION" --profile "$PROFILE"
  aws configure set output json --profile "$PROFILE"
elif [[ -f "$AWS_DIR/credentials" ]] && grep -q '\[default\]' "$AWS_DIR/credentials" 2>/dev/null; then
  echo "==> Credentials file already exists"
else
  echo "No AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in environment."
  echo ""
  echo "Option A — interactive (run in your terminal, not in chat):"
  echo "  aws configure"
  echo "  # Access Key, Secret Key, region: us-east-1, output: json"
  echo ""
  echo "Option B — one-time env vars (do not paste keys into chat):"
  echo "  export AWS_ACCESS_KEY_ID='AKIA...'"
  echo "  export AWS_SECRET_ACCESS_KEY='...'"
  echo "  export AWS_DEFAULT_REGION='us-east-1'"
  echo "  ./deploy/scripts/06-configure-aws.sh"
  echo ""
  echo "Create keys: AWS Console → IAM → Users → Create user → Attach policy"
  echo "  See deploy/iam/terraform-deploy-policy.json"
  exit 1
fi

echo "==> Verifying identity"
aws sts get-caller-identity --region "$REGION" --profile "$PROFILE"

echo ""
echo "AWS CLI is configured for region $REGION (profile: $PROFILE)."
