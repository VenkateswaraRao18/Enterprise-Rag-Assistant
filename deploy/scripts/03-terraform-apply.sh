#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TF_DIR="$ROOT/deploy/terraform"
TF="${TF:-$ROOT/deploy/tools/terraform}"

cd "$TF_DIR"

if [[ ! -f terraform.tfvars ]]; then
  echo "Copy terraform.tfvars.example to terraform.tfvars and edit if needed."
  cp -n terraform.tfvars.example terraform.tfvars 2>/dev/null || true
fi

"$TF" init -upgrade
"$TF" plan -out=tfplan
echo ""
read -r -p "Apply this plan? [y/N] " ans
if [[ "${ans,,}" != "y" ]]; then
  echo "Aborted."
  exit 0
fi

"$TF" apply tfplan
"$TF" output
