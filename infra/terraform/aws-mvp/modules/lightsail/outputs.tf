output "public_ip_address" {
  description = "Public IPv4 address of the Lightsail instance."
  value       = aws_lightsail_instance.this.public_ip_address
}
