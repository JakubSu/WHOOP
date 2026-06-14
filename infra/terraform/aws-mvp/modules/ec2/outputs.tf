output "public_ip_address" {
  description = "Public IPv4 address of the EC2 instance."
  value       = aws_instance.this.public_ip
}

output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.this.id
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch Logs group where Docker container logs are written."
  value       = aws_cloudwatch_log_group.docker.name
}

output "cloudwatch_host_log_group_name" {
  description = "CloudWatch Logs group where EC2 host and deployment logs are written."
  value       = aws_cloudwatch_log_group.host.name
}
