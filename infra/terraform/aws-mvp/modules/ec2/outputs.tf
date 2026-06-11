output "public_ip_address" {
  description = "Public IPv4 address of the EC2 instance."
  value       = aws_instance.this.public_ip
}
