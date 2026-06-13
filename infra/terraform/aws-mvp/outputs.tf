output "app_url" {
  description = "HTTPS URL for the EC2-hosted application."
  value       = local.app_url
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

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC-based application deployments."
  value       = aws_iam_role.github_actions_deploy.arn
}

output "github_actions_oidc_subject" {
  description = "Expected GitHub OIDC subject claim allowed to assume the deploy role."
  value       = local.github_actions_sub
}
