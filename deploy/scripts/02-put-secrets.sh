#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TF_DIR="$ROOT/deploy/terraform"
TF="${TF:-$ROOT/deploy/tools/terraform}"
REGION="${AWS_REGION:-us-east-1}"

cd "$TF_DIR"
SECRET_NAME="$("$TF" output -raw secrets_manager_secret_name)"

python3 << PY
import json
import os
import subprocess
from pathlib import Path

def load_env(path):
    data = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data

env = load_env("$ROOT/.env")
key = env.get("GEMINI_API_KEY", "")
if not key or key == "REPLACE_ME":
    raise SystemExit("GEMINI_API_KEY missing in .env")

payload = {
    "GEMINI_API_KEY": key,
    "API_KEY": env.get("API_KEY", ""),
}
subprocess.run(
    [
        "aws", "secretsmanager", "put-secret-value",
        "--region", "$REGION",
        "--secret-id", "$SECRET_NAME",
        "--secret-string", json.dumps(payload),
    ],
    check=True,
)
print("Secret updated:", "$SECRET_NAME")
PY
