variable "aws_region" {
  description = "AWS region used by the EC2 bootstrap script."
  type        = string
}

variable "instance_name" {
  description = "EC2 instance name."
  type        = string
}

variable "app_directory" {
  description = "Directory on the EC2 instance where the Docker Compose app will be deployed."
  type        = string
}

variable "availability_zone" {
  description = "Availability zone for the application subnet and instance."
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

variable "cloudflare_ipv4_cidrs" {
  description = "Cloudflare IPv4 CIDR ranges allowed to reach web ports."
  type        = list(string)
}

variable "cloudflare_ipv6_cidrs" {
  description = "Cloudflare IPv6 CIDR ranges allowed to reach web ports."
  type        = list(string)
}

variable "ssm_parameter_arns" {
  description = "SSM parameters the EC2 instance can read."
  type        = list(string)
}

variable "cloudwatch_log_group_name" {
  description = "CloudWatch Logs group where Docker container logs are written."
  type        = string
}

variable "cloudwatch_log_retention_days" {
  description = "How many days to retain Docker container logs in CloudWatch."
  type        = number
}

variable "vpc_cidr_block" {
  description = "CIDR block for the dedicated application VPC."
  type        = string
}

variable "subnet_cidr_block" {
  description = "CIDR block for the application public subnet."
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
