output "app_url" {
  description = "HTTPS URL for the EC2-hosted application."
  value       = local.app_url
}

output "marketing_site_url" {
  description = "HTTPS URL for the Cloudflare Pages marketing site."
  value       = "https://${var.marketing_site_domain}"
}

output "marketing_pages_url" {
  description = "Default Cloudflare Pages URL for the marketing project."
  value       = "https://${cloudflare_pages_project.marketing.subdomain}"
}

output "cloudflare_zone_id" {
  description = "Cloudflare zone ID used for the proxied application DNS record."
  value       = data.cloudflare_zone.app.id
}

output "cloudflare_record_hostname" {
  description = "Cloudflare proxied hostname for the application."
  value       = cloudflare_record.app.hostname
}

output "ec2_public_ip_address" {
  description = "Public IPv4 address of the EC2 application instance."
  value       = module.backend.public_ip_address
}

output "ec2_instance_id" {
  description = "Instance ID of the EC2 application host."
  value       = module.backend.instance_id
}

output "ssm_parameter_prefix" {
  description = "SSM Parameter Store prefix used by the application."
  value       = local.ssm_parameter_prefix
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch Logs group where Docker container logs are written."
  value       = module.backend.cloudwatch_log_group_name
}

output "cloudwatch_host_log_group_name" {
  description = "CloudWatch Logs group where EC2 host and deployment logs are written."
  value       = module.backend.cloudwatch_host_log_group_name
}

output "cloudwatch_dashboard_name" {
  description = "CloudWatch dashboard for production operations."
  value       = aws_cloudwatch_dashboard.ops.dashboard_name
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC-based application deployments."
  value       = aws_iam_role.github_actions_deploy.arn
}

output "github_actions_oidc_subject" {
  description = "Expected GitHub OIDC subject claim allowed to assume the deploy role."
  value       = local.github_actions_sub
}

output "ecr_repository_urls" {
  description = "Private ECR repository URLs used for immutable web and API releases."
  value       = { for name, repository in aws_ecr_repository.app : name => repository.repository_url }
}
