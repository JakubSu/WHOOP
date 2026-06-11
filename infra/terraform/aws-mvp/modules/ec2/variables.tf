variable "aws_region" {
  description = "AWS region used by the EC2 bootstrap script."
  type        = string
}

variable "instance_name" {
  description = "EC2 instance name."
  type        = string
}

variable "availability_zone" {
  description = "Availability zone for the backend subnet and instance."
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
}

variable "key_pair_name" {
  description = "Existing EC2 key pair name."
  type        = string
}

variable "allowed_ssh_cidr_blocks" {
  description = "CIDR blocks allowed to connect over SSH."
  type        = list(string)
}

variable "openai_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the OpenAI API key."
  type        = string
}

variable "openai_model" {
  description = "Default OpenAI model stored on the backend host."
  type        = string
}

variable "cors_allowed_origins" {
  description = "Origins allowed by Django CORS configuration."
  type        = list(string)
}

variable "whoop_frontend_allowed_origins" {
  description = "Origins allowed by WHOOP-specific frontend validation."
  type        = list(string)
}

variable "whoop_frontend_success_url" {
  description = "Frontend URL used after WHOOP OAuth success."
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block for the dedicated backend VPC."
  type        = string
}

variable "subnet_cidr_block" {
  description = "CIDR block for the backend public subnet."
  type        = string
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GiB."
  type        = number
}

variable "snapshot_retention_count" {
  description = "How many daily snapshots to retain."
  type        = number
}

variable "snapshot_time_utc" {
  description = "UTC time for the daily snapshot schedule in HH:MM format."
  type        = string
}

variable "tags" {
  description = "Tags applied to EC2-related resources."
  type        = map(string)
  default     = {}
}
