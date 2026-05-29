#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TF_DIR="$ROOT/deploy/terraform"
TF="${TF:-$ROOT/deploy/tools/terraform}"
REGION="${AWS_REGION:-us-east-1}"

cd "$TF_DIR"
CLUSTER="$("$TF" output -raw ecs_cluster_name)"
TASK_DEF="$("$TF" output -raw index_task_definition)"
SUBNETS="$("$TF" output -json private_subnet_ids | python3 -c 'import json,sys; print(",".join(json.load(sys.stdin)))')"
SG="$("$TF" output -raw api_security_group_id)"

echo "==> Running index task (Gemini embed + Qdrant upsert, ~5–10 min)"
TASK_ARN="$(aws ecs run-task \
  --region "$REGION" \
  --cluster "$CLUSTER" \
  --task-definition "$TASK_DEF" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SG],assignPublicIp=ENABLED}" \
  --query 'tasks[0].taskArn' \
  --output text)"

echo "Task: $TASK_ARN"
echo "Waiting for task to stop..."
aws ecs wait tasks-stopped --region "$REGION" --cluster "$CLUSTER" --tasks "$TASK_ARN"

EXIT="$(aws ecs describe-tasks --region "$REGION" --cluster "$CLUSTER" --tasks "$TASK_ARN" \
  --query 'tasks[0].containers[0].exitCode' --output text)"
if [[ "$EXIT" != "0" ]]; then
  echo "Index task failed (exit $EXIT). Logs:"
  echo "  aws logs tail /ecs/techcorp-rag-index --region $REGION --since 30m"
  exit 1
fi
echo "Index task completed successfully."
