data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  amplify_branch_url = "https://${var.amplify_branch_name}.${module.frontend.default_domain}"
  availability_zone  = coalesce(var.ec2_availability_zone, data.aws_availability_zones.available.names[0])
  ec2_key_pair_name  = coalesce(var.ec2_key_pair_name, var.lightsail_ssh_key_pair_name)
  snapshot_time_utc  = coalesce(var.ec2_snapshot_time_utc, var.lightsail_snapshot_time_of_day, "03:00")
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )
}

module "frontend" {
  source = "./modules/amplify"

  amplify_branch_name           = var.amplify_branch_name
  amplify_environment_variables = var.amplify_environment_variables
  auto_branch_deletion_enabled  = var.auto_branch_deletion_enabled
  auto_build_enabled            = var.auto_build_enabled
  environment                   = var.environment
  framework                     = "React"
  oauth_token                   = var.github_oauth_token
  platform                      = "WEB"
  project_name                  = var.project_name
  repository                    = var.github_repository
  stage                         = "PRODUCTION"
  tags                          = local.common_tags
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "/${var.project_name}/${var.environment}/backend/openai-api-key"
  description             = "OpenAI API key for the ${var.project_name} ${var.environment} backend."
  recovery_window_in_days = var.secrets_manager_recovery_window_in_days

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id                = aws_secretsmanager_secret.openai_api_key.id
  secret_string_wo         = var.openai_api_key
  secret_string_wo_version = var.openai_api_key_version
}

module "backend" {
  source = "./modules/ec2"

  allowed_ssh_cidr_blocks        = var.allowed_ssh_cidr_blocks
  availability_zone              = local.availability_zone
  aws_region                     = var.aws_region
  cors_allowed_origins           = concat(var.additional_cors_allowed_origins, [local.amplify_branch_url])
  instance_name                  = "${var.project_name}-${var.environment}-backend"
  instance_type                  = var.ec2_instance_type
  key_pair_name                  = local.ec2_key_pair_name
  openai_model                   = var.openai_model
  openai_secret_arn              = aws_secretsmanager_secret.openai_api_key.arn
  root_volume_size_gb            = var.ec2_root_volume_size_gb
  snapshot_retention_count       = var.ec2_snapshot_retention_count
  snapshot_time_utc              = local.snapshot_time_utc
  subnet_cidr_block              = var.ec2_subnet_cidr_block
  tags                           = local.common_tags
  vpc_cidr_block                 = var.ec2_vpc_cidr_block
  whoop_frontend_allowed_origins = concat(var.additional_whoop_frontend_allowed_origins, [local.amplify_branch_url])
  whoop_frontend_success_url     = "${local.amplify_branch_url}${var.whoop_frontend_success_path}"
}
