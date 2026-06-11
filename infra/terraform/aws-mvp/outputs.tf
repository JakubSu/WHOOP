output "amplify_app_default_domain" {
  description = "Amplify default domain assigned to the app."
  value       = module.frontend.default_domain
}

output "amplify_default_url" {
  description = "Default hosted URL for the configured Amplify branch."
  value       = local.amplify_branch_url
}

output "lightsail_public_ip_address" {
  description = "Public IPv4 address of the Lightsail backend instance."
  value       = module.backend.public_ip_address
}
