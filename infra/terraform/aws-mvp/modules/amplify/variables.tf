variable "project_name" {
  description = "Short project identifier used in resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "repository" {
  description = "GitHub repository URL connected to Amplify."
  type        = string
}

variable "oauth_token" {
  description = "GitHub OAuth token used by Amplify."
  type        = string
  sensitive   = true
}

variable "platform" {
  description = "Amplify platform value."
  type        = string
}

variable "framework" {
  description = "Amplify framework metadata."
  type        = string
}

variable "stage" {
  description = "Amplify branch stage."
  type        = string
}

variable "amplify_branch_name" {
  description = "Git branch Amplify should build and deploy."
  type        = string
}

variable "amplify_environment_variables" {
  description = "Additional Amplify environment variables."
  type        = map(string)
  default     = {}
}

variable "auto_build_enabled" {
  description = "Whether Amplify should auto-build on pushes."
  type        = bool
}

variable "auto_branch_deletion_enabled" {
  description = "Whether Amplify should delete preview branches automatically."
  type        = bool
}

variable "tags" {
  description = "Tags applied to Amplify resources."
  type        = map(string)
  default     = {}
}
