data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  availability_zone    = coalesce(var.ec2_availability_zone, data.aws_availability_zones.available.names[0])
  ec2_key_pair_name    = coalesce(var.ec2_key_pair_name, var.lightsail_ssh_key_pair_name)
  snapshot_time_utc    = coalesce(var.ec2_snapshot_time_utc, var.lightsail_snapshot_time_of_day, "03:00")
  domain_name          = trimsuffix(var.domain_name, ".")
  cloudflare_zone_name = trimsuffix(var.cloudflare_zone_name, ".")
  app_url              = "https://${local.domain_name}"
  ssm_parameter_prefix = "/${var.project_name}/${var.environment}"
  github_actions_sub   = "repo:${var.github_repository}:environment:${var.github_actions_environment}"
  cloudwatch_log_group = "${local.ssm_parameter_prefix}/docker"
  host_log_group       = "${local.ssm_parameter_prefix}/host"
  ecr_repositories = {
    web = "${var.project_name}/web"
    api = "${var.project_name}/api"
  }
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )
}

data "cloudflare_zone" "app" {
  name = local.cloudflare_zone_name
}

data "cloudflare_ip_ranges" "cloudflare" {
}

data "tls_certificate" "github_actions" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_ses_email_identity" "whoop_access_request_sender" {
  email = var.ses_from_email
}

resource "aws_ssm_parameter" "django_secret_key" {
  name        = "${local.ssm_parameter_prefix}/django/secret-key"
  description = "Django SECRET_KEY for ${var.project_name} ${var.environment}."
  type        = "SecureString"
  value       = var.django_secret_key

  tags = local.common_tags
}

resource "aws_ssm_parameter" "openai_api_key" {
  name        = "${local.ssm_parameter_prefix}/openai/api-key"
  description = "OpenAI API key for ${var.project_name} ${var.environment}."
  type        = "SecureString"
  value       = var.openai_api_key

  tags = local.common_tags
}

resource "aws_ssm_parameter" "logfire_token" {
  name        = "${local.ssm_parameter_prefix}/logfire/token"
  description = "Logfire write token for ${var.project_name} ${var.environment}."
  type        = "SecureString"
  value       = var.logfire_token

  tags = local.common_tags
}

resource "aws_ssm_parameter" "whoop_client_id" {
  name        = "${local.ssm_parameter_prefix}/whoop/client-id"
  description = "WHOOP OAuth client ID for ${var.project_name} ${var.environment}."
  type        = "String"
  value       = var.whoop_client_id

  tags = local.common_tags
}

resource "aws_ssm_parameter" "whoop_client_secret" {
  name        = "${local.ssm_parameter_prefix}/whoop/client-secret"
  description = "WHOOP OAuth client secret for ${var.project_name} ${var.environment}."
  type        = "SecureString"
  value       = var.whoop_client_secret

  tags = local.common_tags
}

resource "aws_ssm_parameter" "whoop_token_encryption_key" {
  name        = "${local.ssm_parameter_prefix}/whoop/token-encryption-key"
  description = "WHOOP token encryption key for ${var.project_name} ${var.environment}."
  type        = "SecureString"
  value       = var.whoop_token_encryption_key

  tags = local.common_tags
}

resource "aws_ssm_parameter" "postgres_password" {
  name        = "${local.ssm_parameter_prefix}/postgres/password"
  description = "Postgres password for ${var.project_name} ${var.environment}."
  type        = "SecureString"
  value       = var.postgres_password

  tags = local.common_tags
}

resource "aws_ssm_parameter" "ses_from_email" {
  name        = "${local.ssm_parameter_prefix}/ses/from-email"
  description = "Verified SES sender email for ${var.project_name} ${var.environment}."
  type        = "String"
  value       = var.ses_from_email

  tags = local.common_tags
}

resource "aws_ssm_parameter" "whoop_access_allowlist" {
  name        = "${local.ssm_parameter_prefix}/whoop/access-allowlist"
  description = "Comma-separated WHOOP access allowlist for ${var.project_name} ${var.environment}."
  type        = "String"
  value       = var.whoop_access_allowlist

  tags = local.common_tags
}

resource "aws_ssm_parameter" "whoop_access_request_admin_email" {
  name        = "${local.ssm_parameter_prefix}/whoop/access-request-admin-email"
  description = "WHOOP access request notification recipient for ${var.project_name} ${var.environment}."
  type        = "String"
  value       = var.whoop_access_request_admin_email

  tags = local.common_tags
}

resource "aws_ecr_repository" "app" {
  for_each = local.ecr_repositories

  name                 = each.value
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(local.common_tags, { Service = each.key })
}

resource "aws_ecr_lifecycle_policy" "app" {
  for_each = aws_ecr_repository.app

  repository = each.value.name
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Delete untagged image artifacts after one day."
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep the three newest immutable commit releases."
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["sha-"]
          countType     = "imageCountMoreThan"
          countNumber   = 3
        }
        action = { type = "expire" }
      },
    ]
  })
}

module "backend" {
  source = "./modules/ec2"

  allowed_ssh_cidr_blocks        = var.allowed_ssh_cidr_blocks
  app_directory                  = "/opt/whoop-ai-coach"
  availability_zone              = local.availability_zone
  aws_region                     = var.aws_region
  cloudwatch_host_log_group_name = local.host_log_group
  cloudwatch_log_group_name      = local.cloudwatch_log_group
  cloudwatch_log_retention_days  = var.cloudwatch_log_retention_days
  cloudflare_ipv4_cidrs          = data.cloudflare_ip_ranges.cloudflare.ipv4_cidr_blocks
  cloudflare_ipv6_cidrs          = data.cloudflare_ip_ranges.cloudflare.ipv6_cidr_blocks
  ecr_repository_arns            = [for repository in aws_ecr_repository.app : repository.arn]
  instance_name                  = "${var.project_name}-${var.environment}-backend"
  instance_type                  = var.ec2_instance_type
  key_pair_name                  = local.ec2_key_pair_name
  root_volume_size_gb            = var.ec2_root_volume_size_gb
  ses_from_email                 = var.ses_from_email
  snapshot_retention_count       = var.ec2_snapshot_retention_count
  snapshot_time_utc              = local.snapshot_time_utc
  ssm_parameter_arns = [
    aws_ssm_parameter.django_secret_key.arn,
    aws_ssm_parameter.openai_api_key.arn,
    aws_ssm_parameter.logfire_token.arn,
    aws_ssm_parameter.whoop_client_id.arn,
    aws_ssm_parameter.whoop_client_secret.arn,
    aws_ssm_parameter.whoop_token_encryption_key.arn,
    aws_ssm_parameter.postgres_password.arn,
    aws_ssm_parameter.whoop_access_allowlist.arn,
    aws_ssm_parameter.ses_from_email.arn,
    aws_ssm_parameter.whoop_access_request_admin_email.arn,
  ]
  subnet_cidr_block = var.ec2_subnet_cidr_block
  tags              = local.common_tags
  vpc_cidr_block    = var.ec2_vpc_cidr_block
}

resource "aws_cloudwatch_dashboard" "ops" {
  dashboard_name = "${var.project_name}-${var.environment}-ops"

  dashboard_body = jsonencode({
    start          = "-PT6H"
    periodOverride = "inherit"
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "EC2 CPU"
          region = var.aws_region
          period = 300
          stat   = "Average"
          view   = "timeSeries"
          metrics = [
            ["AWS/EC2", "CPUUtilization", "InstanceId", module.backend.instance_id],
          ]
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "EC2 Status Checks"
          region = var.aws_region
          period = 300
          stat   = "Maximum"
          view   = "timeSeries"
          metrics = [
            ["AWS/EC2", "StatusCheckFailed", "InstanceId", module.backend.instance_id],
            [".", "StatusCheckFailed_Instance", ".", "."],
            [".", "StatusCheckFailed_System", ".", "."],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "Host Memory"
          region = var.aws_region
          period = 300
          stat   = "Average"
          view   = "timeSeries"
          metrics = [
            [{
              expression = "SEARCH('{CWAgent,InstanceId} MetricName=\"mem_used_percent\" InstanceId=\"${module.backend.instance_id}\"', 'Average', 300)"
              id         = "mem"
              label      = "Memory used %"
            }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "Root Disk"
          region = var.aws_region
          period = 300
          stat   = "Average"
          view   = "timeSeries"
          metrics = [
            [{
              expression = "SEARCH('{CWAgent,InstanceId,path} MetricName=\"disk_used_percent\" InstanceId=\"${module.backend.instance_id}\" path=\"/\"', 'Average', 300)"
              id         = "disk"
              label      = "Root disk used %"
            }],
          ]
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Latest Deployment Logs"
          region = var.aws_region
          view   = "table"
          query  = "SOURCE '${local.host_log_group}' | fields @timestamp, @message | filter @logStream like /deploy/ | sort @timestamp desc | limit 50"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Deployment Errors"
          region = var.aws_region
          view   = "table"
          query  = "SOURCE '${local.host_log_group}' | fields @timestamp, @message | filter @logStream like /deploy/ | filter @message like /(?i)(error|failed|traceback|exception|timed out|exit code|nonzero)/ | sort @timestamp desc | limit 50"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Latest API Logs"
          region = var.aws_region
          view   = "table"
          query  = "SOURCE '${local.cloudwatch_log_group}' | fields @timestamp, @message | filter @logStream = 'api' | sort @timestamp desc | limit 50"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "API Errors"
          region = var.aws_region
          view   = "table"
          query  = "SOURCE '${local.cloudwatch_log_group}' | fields @timestamp, @message | filter @logStream = 'api' | filter @message like /(?i)(error|exception|traceback| 500 |AIProviderConfigurationError|openai|whoop|database|connection refused|timeout)/ | sort @timestamp desc | limit 50"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 18
        width  = 12
        height = 6
        properties = {
          title  = "Latest Host Logs"
          region = var.aws_region
          view   = "table"
          query  = "SOURCE '${local.host_log_group}' | fields @timestamp, @logStream, @message | filter @logStream like /syslog|cloud-init-output|docker-daemon/ | sort @timestamp desc | limit 50"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 18
        width  = 12
        height = 6
        properties = {
          title  = "Host Crash Signals"
          region = var.aws_region
          view   = "table"
          query  = "SOURCE '${local.host_log_group}' | fields @timestamp, @logStream, @message | filter @message like /(?i)(oom|killed process|segfault|panic|failed|unhealthy|No space left|systemd|docker.*restart|docker.*fail)/ | sort @timestamp desc | limit 50"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 24
        width  = 12
        height = 6
        properties = {
          title  = "Caddy Ingress Logs"
          region = var.aws_region
          view   = "table"
          query  = "SOURCE '${local.cloudwatch_log_group}' | fields @timestamp, @message | filter @logStream = 'caddy' | sort @timestamp desc | limit 50"
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 24
        width  = 12
        height = 6
        properties = {
          title  = "Postgres Logs"
          region = var.aws_region
          view   = "table"
          query  = "SOURCE '${local.cloudwatch_log_group}' | fields @timestamp, @message | filter @logStream = 'db' | sort @timestamp desc | limit 50"
        }
      },
    ]
  })
}

resource "cloudflare_record" "app" {
  zone_id = data.cloudflare_zone.app.id
  name    = var.cloudflare_record_name
  content = module.backend.public_ip_address
  type    = "A"
  proxied = true
  ttl     = 1
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    data.tls_certificate.github_actions.certificates[0].sha1_fingerprint,
  ]

  tags = local.common_tags
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    effect = "Allow"

    actions = [
      "sts:AssumeRoleWithWebIdentity",
    ]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.github_actions_sub]
    }
  }
}

resource "aws_iam_role" "github_actions_deploy" {
  name               = "${var.project_name}-${var.environment}-github-actions-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json

  tags = local.common_tags
}

data "aws_iam_policy_document" "github_actions_deploy" {
  statement {
    sid       = "DiscoverBackendInstance"
    effect    = "Allow"
    actions   = ["ec2:DescribeInstances"]
    resources = ["*"]
  }

  statement {
    sid       = "AuthenticateToEcr"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid    = "PublishReleaseImages"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [for repository in aws_ecr_repository.app : repository.arn]
  }

  statement {
    sid    = "SendSsmRunCommandToBackend"
    effect = "Allow"

    actions = [
      "ssm:SendCommand",
    ]

    resources = [
      "arn:${data.aws_partition.current.partition}:ssm:${var.aws_region}::document/AWS-RunShellScript",
      "arn:${data.aws_partition.current.partition}:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/${module.backend.instance_id}",
    ]
  }

  statement {
    sid    = "ReadSsmCommandStatus"
    effect = "Allow"

    actions = [
      "ssm:GetCommandInvocation",
      "ssm:ListCommandInvocations",
      "ssm:ListCommands",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_actions_deploy" {
  name   = "${var.project_name}-${var.environment}-github-actions-deploy"
  role   = aws_iam_role.github_actions_deploy.id
  policy = data.aws_iam_policy_document.github_actions_deploy.json
}
