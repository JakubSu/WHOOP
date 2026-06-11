locals {
  backend_directory = "/var/www/backend"
  django_user       = "django"
}

resource "aws_lightsail_instance" "this" {
  name              = var.instance_name
  availability_zone = var.availability_zone
  blueprint_id      = var.blueprint_id
  bundle_id         = var.bundle_id
  key_pair_name     = var.ssh_key_pair_name

  user_data = templatefile("${path.module}/templates/user_data.sh.tftpl", {
    app_directory                     = local.backend_directory
    cors_allowed_origins              = join(",", distinct(var.cors_allowed_origins))
    django_user                       = local.django_user
    openai_api_key_b64                = base64encode(var.openai_api_key)
    openai_model                      = var.openai_model
    whoop_frontend_allowed_origins    = join(",", distinct(var.whoop_frontend_allowed_origins))
    whoop_frontend_success_url        = var.whoop_frontend_success_url
  })

  add_on {
    type            = "AutoSnapshot"
    snapshot_time_of_day = var.snapshot_time_of_day
    status          = "Enabled"
  }

  tags = var.tags
}

resource "aws_lightsail_instance_public_ports" "this" {
  instance_name = aws_lightsail_instance.this.name

  port_info {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    cidrs     = ["0.0.0.0/0"]
  }

  port_info {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidrs     = ["0.0.0.0/0"]
  }

  port_info {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"
    cidrs     = var.allowed_ssh_cidr_blocks
  }
}
