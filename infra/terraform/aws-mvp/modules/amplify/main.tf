locals {
  app_name = "${var.project_name}-${var.environment}-web"
}

data "aws_iam_policy_document" "amplify_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["amplify.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "amplify" {
  name               = "${local.app_name}-service-role"
  assume_role_policy = data.aws_iam_policy_document.amplify_assume_role.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "amplify" {
  role       = aws_iam_role.amplify.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess-Amplify"
}

resource "aws_amplify_app" "this" {
  name                        = local.app_name
  repository                  = var.repository
  access_token                = var.oauth_token
  iam_service_role_arn        = aws_iam_role.amplify.arn
  platform                    = var.platform
  enable_branch_auto_deletion = var.auto_branch_deletion_enabled
  environment_variables       = var.amplify_environment_variables

  build_spec = <<-EOT
    version: 1
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci --prefix apps/web
        build:
          commands:
            - npm run build --prefix apps/web
      artifacts:
        baseDirectory: apps/web/dist
        files:
          - '**/*'
      cache:
        paths:
          - apps/web/node_modules/**/*
  EOT

  custom_rule {
    source = "/<*>"
    target = "/index.html"
    status = "404-200"
  }

  tags = var.tags
}

resource "aws_amplify_branch" "this" {
  app_id            = aws_amplify_app.this.id
  branch_name       = var.amplify_branch_name
  framework         = var.framework
  stage             = var.stage
  enable_auto_build = var.auto_build_enabled

  tags = var.tags
}
