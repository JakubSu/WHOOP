data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ssm_parameter_access" {
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]
    resources = var.ssm_parameter_arns
  }

  statement {
    actions   = ["kms:Decrypt"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.aws_region}.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "cloudwatch_logs_access" {
  statement {
    actions   = ["logs:DescribeLogGroups"]
    resources = ["*"]
  }

  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
    ]
    resources = [
      aws_cloudwatch_log_group.docker.arn,
      "${aws_cloudwatch_log_group.docker.arn}:*",
      aws_cloudwatch_log_group.host.arn,
      "${aws_cloudwatch_log_group.host.arn}:*",
    ]
  }

  statement {
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["CWAgent"]
    }
  }

  statement {
    actions   = ["ec2:DescribeTags"]
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "ecr_pull_access" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = var.ecr_repository_arns
  }
}

data "aws_iam_policy_document" "dlm_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["dlm.amazonaws.com"]
    }
  }
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, { Name = "${var.instance_name}-vpc" })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, { Name = "${var.instance_name}-igw" })
}

resource "aws_subnet" "this" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.subnet_cidr_block
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = merge(var.tags, { Name = "${var.instance_name}-subnet" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(var.tags, { Name = "${var.instance_name}-public-rt" })
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.this.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "backend" {
  name        = "${var.instance_name}-sg"
  description = "Cloudflare web ingress and restricted SSH."
  vpc_id      = aws_vpc.this.id

  ingress {
    description      = "HTTP from Cloudflare proxy"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = var.cloudflare_ipv4_cidrs
    ipv6_cidr_blocks = var.cloudflare_ipv6_cidrs
  }

  ingress {
    description      = "HTTPS from Cloudflare proxy"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = var.cloudflare_ipv4_cidrs
    ipv6_cidr_blocks = var.cloudflare_ipv6_cidrs
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr_blocks
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.instance_name}-sg" })
}

resource "aws_cloudwatch_log_group" "docker" {
  name              = var.cloudwatch_log_group_name
  retention_in_days = var.cloudwatch_log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "host" {
  name              = var.cloudwatch_host_log_group_name
  retention_in_days = var.cloudwatch_log_retention_days

  tags = var.tags
}

resource "aws_iam_role" "ec2" {
  name               = "${var.instance_name}-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = var.tags
}

resource "aws_iam_role_policy" "ssm_parameter_access" {
  name   = "${var.instance_name}-ssm-parameter-access"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ssm_parameter_access.json
}

resource "aws_iam_role_policy" "cloudwatch_logs_access" {
  name   = "${var.instance_name}-cloudwatch-logs-access"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.cloudwatch_logs_access.json
}

resource "aws_iam_role_policy" "ecr_pull_access" {
  name   = "${var.instance_name}-ecr-pull-access"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ecr_pull_access.json
}

resource "aws_iam_role_policy_attachment" "ssm_managed_instance_core" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.instance_name}-profile"
  role = aws_iam_role.ec2.name

  tags = var.tags
}

resource "aws_instance" "this" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.this.id
  vpc_security_group_ids      = [aws_security_group.backend.id]
  key_name                    = var.key_pair_name
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  associate_public_ip_address = true
  user_data_replace_on_change = true

  user_data = templatefile("${path.module}/templates/user_data.sh.tftpl", {
    app_directory                  = var.app_directory
    aws_region                     = var.aws_region
    cloudwatch_host_log_group_name = var.cloudwatch_host_log_group_name
  })

  root_block_device {
    volume_size           = var.root_volume_size_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = false
    tags                  = merge(var.tags, { Snapshot = "true" })
  }

  tags = merge(var.tags, {
    Name     = var.instance_name
    Snapshot = "true"
  })

  lifecycle {
    ignore_changes = [ami]
  }
}

resource "aws_iam_role" "dlm" {
  name               = "${var.instance_name}-dlm-role"
  assume_role_policy = data.aws_iam_policy_document.dlm_assume_role.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "dlm" {
  role       = aws_iam_role.dlm.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSDataLifecycleManagerServiceRole"
}

resource "aws_dlm_lifecycle_policy" "root_volume_snapshots" {
  description        = "Daily root volume snapshots"
  execution_role_arn = aws_iam_role.dlm.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]
    target_tags = {
      Snapshot = "true"
    }

    schedule {
      name = "daily-root-volume-snapshots"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = [var.snapshot_time_utc]
      }

      retain_rule {
        count = var.snapshot_retention_count
      }

      copy_tags = true
    }
  }

  tags = var.tags
}
