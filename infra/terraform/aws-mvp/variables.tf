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

variable "domain_name" {
  description = "Public application domain name, for example app.example.com."
  type        = string
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with permission to read the zone and manage DNS records."
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_name" {
  description = "Cloudflare zone name, for example example.com."
  type        = string
}

variable "cloudflare_record_name" {
  description = "Cloudflare DNS record name, for example app for app.example.com or @ for the zone apex."
  type        = string
}

variable "github_repository" {
  description = "GitHub repository allowed to assume the deploy role, in owner/name format."
  type        = string
  default     = "JakubSu/WHOOP"
}

variable "github_actions_environment" {
  description = "GitHub Actions environment name allowed to assume the deploy role."
  type        = string
  default     = "production"
}

variable "ec2_availability_zone" {
  description = "Optional EC2 availability zone. Leave null to use the first available zone in the AWS region."
  type        = string
  default     = null
}

variable "ec2_instance_type" {
  description = "EC2 instance type for the Docker Compose host."
  type        = string
  default     = "t3.micro"
}

variable "ec2_key_pair_name" {
  description = "Existing EC2 key pair name for administrative SSH access."
  type        = string
  default     = null
}

variable "ec2_vpc_cidr_block" {
  description = "CIDR block for the dedicated application VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "ec2_subnet_cidr_block" {
  description = "CIDR block for the public application subnet."
  type        = string
  default     = "10.42.1.0/24"
}

variable "ec2_root_volume_size_gb" {
  description = "Root EBS volume size for the Docker Compose host in GiB."
  type        = number
  default     = 24
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

variable "django_secret_key" {
  description = "Production Django SECRET_KEY written to SSM Parameter Store."
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "Production OpenAI API key written to SSM Parameter Store."
  type        = string
  sensitive   = true
}

variable "whoop_client_id" {
  description = "Production WHOOP OAuth client ID written to SSM Parameter Store."
  type        = string
}

variable "whoop_client_secret" {
  description = "Production WHOOP OAuth client secret written to SSM Parameter Store."
  type        = string
  sensitive   = true
}

variable "whoop_token_encryption_key" {
  description = "Production Fernet key used to encrypt WHOOP tokens, written to SSM Parameter Store."
  type        = string
  sensitive   = true
}

variable "postgres_password" {
  description = "Production Postgres password written to SSM Parameter Store."
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Additional tags applied to all supported resources."
  type        = map(string)
  default     = {}
}
