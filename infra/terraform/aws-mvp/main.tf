data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  amplify_branch_url = "https://${var.amplify_branch_name}.${module.frontend.default_domain}"
  availability_zone  = coalesce(var.lightsail_availability_zone, data.aws_availability_zones.available.names[0])
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

  amplify_branch_name            = var.amplify_branch_name
  amplify_environment_variables  = var.amplify_environment_variables
  auto_branch_deletion_enabled   = var.auto_branch_deletion_enabled
  auto_build_enabled             = var.auto_build_enabled
  environment                    = var.environment
  framework                      = "React"
  oauth_token                    = var.github_oauth_token
  platform                       = "WEB"
  project_name                   = var.project_name
  repository                     = var.github_repository
  stage                          = "PRODUCTION"
  tags                           = local.common_tags
}

module "backend" {
  source = "./modules/lightsail"

  allowed_ssh_cidr_blocks         = var.allowed_ssh_cidr_blocks
  availability_zone               = local.availability_zone
  blueprint_id                    = var.lightsail_blueprint_id
  bundle_id                       = var.lightsail_bundle_id
  cors_allowed_origins            = concat(var.additional_cors_allowed_origins, [local.amplify_branch_url])
  instance_name                   = "${var.project_name}-${var.environment}-backend"
  openai_api_key                  = var.openai_api_key
  openai_model                    = var.openai_model
  snapshot_time_of_day            = var.lightsail_snapshot_time_of_day
  ssh_key_pair_name               = var.lightsail_ssh_key_pair_name
  tags                            = local.common_tags
  whoop_frontend_allowed_origins  = concat(var.additional_whoop_frontend_allowed_origins, [local.amplify_branch_url])
  whoop_frontend_success_url      = "${local.amplify_branch_url}${var.whoop_frontend_success_path}"
}
