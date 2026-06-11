output "app_id" {
  description = "Amplify app ID."
  value       = aws_amplify_app.this.id
}

output "default_domain" {
  description = "Amplify default domain for the app."
  value       = aws_amplify_app.this.default_domain
}
