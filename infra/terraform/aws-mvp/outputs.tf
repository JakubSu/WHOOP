output "amplify_app_default_domain" {
  description = "Amplify default domain assigned to the app."
  value       = module.frontend.default_domain
}

output "amplify_default_url" {
  description = "Default hosted URL for the configured Amplify branch."
  value       = local.amplify_branch_url
}

output "ec2_public_ip_address" {
  description = "Public IPv4 address of the EC2 backend instance."
  value       = module.backend.public_ip_address
}

output "openai_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the backend OpenAI API key."
  value       = aws_secretsmanager_secret.openai_api_key.arn
}
