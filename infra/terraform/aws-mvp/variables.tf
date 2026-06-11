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

variable "ec2_availability_zone" {
  description = "Optional EC2 availability zone. Leave null to use the first available zone in the AWS region."
  type        = string
  default     = null
}

variable "ec2_instance_type" {
  description = "EC2 instance type for the backend host."
  type        = string
  default     = "t3.micro"
}

variable "ec2_key_pair_name" {
  description = "Existing EC2 key pair name for administrative SSH access."
  type        = string
  default     = null
}

variable "ec2_vpc_cidr_block" {
  description = "CIDR block for the dedicated backend VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "ec2_subnet_cidr_block" {
  description = "CIDR block for the public backend subnet."
  type        = string
  default     = "10.42.1.0/24"
}

variable "ec2_root_volume_size_gb" {
  description = "Root EBS volume size for the backend instance in GiB."
  type        = number
  default     = 16
}

variable "ec2_snapshot_retention_count" {
  description = "How many daily snapshots to retain for the backend root volume."
  type        = number
  default     = 7
}

variable "ec2_snapshot_time_utc" {
  description = "UTC time for the daily EBS snapshot policy in HH:MM format."
  type        = string
  default     = null
}

variable "allowed_ssh_cidr_blocks" {
  description = "CIDR blocks allowed to reach the instance over SSH."
  type        = list(string)
}

variable "lightsail_ssh_key_pair_name" {
  description = "Deprecated compatibility variable for the previous Lightsail-based module."
  type        = string
  default     = null
}

variable "lightsail_snapshot_time_of_day" {
  description = "Deprecated compatibility variable for the previous Lightsail-based module."
  type        = string
  default     = null
}

variable "secrets_manager_recovery_window_in_days" {
  description = "Recovery window for deleting the Secrets Manager secret."
  type        = number
  default     = 7
}

variable "openai_api_key" {
  description = "Production OpenAI API key written to AWS Secrets Manager without persisting the value in Terraform state."
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "openai_api_key_version" {
  description = "Monotonic version number for rotating the write-only OpenAI API key secret."
  type        = number
  default     = 1
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
