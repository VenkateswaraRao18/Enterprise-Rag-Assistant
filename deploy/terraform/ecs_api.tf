locals {
  api_environment = [
    { name = "LLM_PROVIDER", value = "gemini" },
    { name = "QDRANT_URL", value = "http://qdrant.techcorp.local:6333" },
    { name = "QDRANT_COLLECTION", value = "techcorp_docs" },
    { name = "GEMINI_CHAT_MODEL", value = "gemini-2.5-flash" },
    { name = "GEMINI_EMBED_MODEL", value = "gemini-embedding-001" },
    { name = "CORS_ORIGINS", value = var.cors_origins },
    { name = "API_HOST", value = "0.0.0.0" },
    { name = "API_PORT", value = "8080" },
  ]

  api_secrets = [
    {
      name      = "GEMINI_API_KEY"
      valueFrom = "${aws_secretsmanager_secret.app.arn}:GEMINI_API_KEY::"
    },
    {
      name      = "API_KEY"
      valueFrom = "${aws_secretsmanager_secret.app.arn}:API_KEY::"
    },
  ]
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = local.api_image
      essential = true
      portMappings = [
        {
          containerPort = 8080
          hostPort      = 8080
          protocol      = "tcp"
        }
      ]
      environment = local.api_environment
      secrets     = local.api_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [for s in data.aws_subnet.selected : s.id]
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8080
  }

  depends_on = [
    aws_lb_listener.http,
    aws_ecs_service.qdrant,
  ]

  tags = local.common_tags
}

resource "aws_ecs_task_definition" "index" {
  family                   = "${local.name_prefix}-index"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "index"
      image     = local.api_image
      essential = true
      command   = ["python", "-m", "app.index_embeddings", "--recreate"]
      environment = concat(local.api_environment, [
        { name = "EMBED_BATCH_SIZE", value = "8" },
      ])
      secrets = local.api_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.index.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "index"
        }
      }
    }
  ])

  tags = local.common_tags
}
