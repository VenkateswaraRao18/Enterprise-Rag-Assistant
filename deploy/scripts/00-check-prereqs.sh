#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Checking prerequisites for Path B (us-east-1)"

missing=0
for cmd in aws docker terraform; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  OK  $cmd ($($(command -v "$cmd") 2>/dev/null || echo $cmd))"
  else
    echo "  MISSING  $cmd"
    missing=1
  fi
done

if [[ $missing -eq 1 ]]; then
  echo ""
  echo "Install missing tools:"
  echo "  AWS CLI:  https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
  echo "  Docker:   https://docs.docker.com/get-docker/"
  echo "  Terraform: https://developer.hashicorp.com/terraform/install"
  exit 1
fi

echo "==> AWS identity"
aws sts get-caller-identity --region us-east-1

if [[ ! -f "$ROOT/.env" ]]; then
  echo "WARN: $ROOT/.env not found — copy from .env.example and set GEMINI_API_KEY"
  exit 1
fi

echo "==> All checks passed"
