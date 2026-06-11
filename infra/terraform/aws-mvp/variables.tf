variable "aws_region" {
  description = "AWS region for the MVP deployment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short project identifier used in resource naming."
  type        = string
  default     = "whoop-ai-coach"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "github_repository" {
  description = "GitHub repository URL connected to AWS Amplify."
  type        = string
}

variable "github_oauth_token" {
  description = "GitHub OAuth token used by AWS Amplify to access the repository."
  type        = string
  sensitive   = true
}

variable "amplify_branch_name" {
  description = "Git branch Amplify should build and deploy."
  type        = string
  default     = "main"
}

variable "amplify_environment_variables" {
  description = "Additional environment variables injected into the Amplify build."
  type        = map(string)
  default     = {}
}

variable "auto_build_enabled" {
  description = "Whether Amplify should auto-build on pushes to the configured branch."
  type        = bool
  default     = true
}

variable "auto_branch_deletion_enabled" {
  description = "Whether Amplify should delete preview branches automatically after branch deletion."
  type        = bool
  default     = true
}

variable "lightsail_availability_zone" {
  description = "Optional Lightsail availability zone. Leave null to use the first available zone in the AWS region."
  type        = string
  default     = null
}

variable "lightsail_blueprint_id" {
  description = "Lightsail blueprint ID for the backend instance."
  type        = string
  default     = "ubuntu_24_04"
}

variable "lightsail_bundle_id" {
  description = "Lightsail bundle ID tuned for low-cost MVP usage."
  type        = string
  default     = "micro_1_0"
}

variable "lightsail_ssh_key_pair_name" {
  description = "Existing Lightsail SSH key pair name."
  type        = string
}

variable "allowed_ssh_cidr_blocks" {
  description = "CIDR blocks allowed to reach the instance over SSH."
  type        = list(string)
}

variable "lightsail_snapshot_time_of_day" {
  description = "UTC time for the daily automatic Lightsail snapshot in HH:MM format."
  type        = string
  default     = "03:00"
}

variable "openai_api_key" {
  description = "Production OpenAI API key written to the backend .env file during instance bootstrap."
  type        = string
  sensitive   = true
}

variable "openai_model" {
  description = "Default OpenAI model name written to the backend .env file."
  type        = string
  default     = "gpt-4.1-mini"
}

variable "whoop_frontend_success_path" {
  description = "Frontend path used after WHOOP OAuth success."
  type        = string
  default     = "/connect-whoop/success"
}

variable "additional_cors_allowed_origins" {
  description = "Extra backend CORS origins to allow in addition to the Amplify branch URL."
  type        = list(string)
  default     = []
}

variable "additional_whoop_frontend_allowed_origins" {
  description = "Extra frontend origins allowed by WHOOP-specific backend settings in addition to the Amplify branch URL."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags applied to all supported resources."
  type        = map(string)
  default     = {}
}
