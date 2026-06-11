variable "instance_name" {
  description = "Lightsail instance name."
  type        = string
}

variable "availability_zone" {
  description = "Lightsail availability zone."
  type        = string
}

variable "blueprint_id" {
  description = "Lightsail blueprint ID."
  type        = string
}

variable "bundle_id" {
  description = "Lightsail bundle ID."
  type        = string
}

variable "ssh_key_pair_name" {
  description = "Existing Lightsail SSH key pair name."
  type        = string
}

variable "allowed_ssh_cidr_blocks" {
  description = "CIDR blocks allowed to connect over SSH."
  type        = list(string)
}

variable "snapshot_time_of_day" {
  description = "UTC time for the daily Lightsail snapshot in HH:MM format."
  type        = string
}

variable "openai_api_key" {
  description = "OpenAI API key stored on the backend host."
  type        = string
  sensitive   = true
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

variable "tags" {
  description = "Tags applied to Lightsail resources."
  type        = map(string)
  default     = {}
}
