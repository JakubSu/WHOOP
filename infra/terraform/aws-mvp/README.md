# AWS MVP Terraform

This stack provisions the single-instance AWS deployment:

- React UI, Django API, Caddy, and Postgres on one EC2 instance through Docker Compose
- HTTPS through Cloudflare proxy mode in front of Caddy
- Cloudflare proxied app `A` record
- Production secrets and app parameters in SSM Parameter Store
- Docker container logs in CloudWatch Logs
- EC2 IAM role scoped to the app SSM parameters
- GitHub Actions OIDC role for building immutable ECR images and SSM-based app deployments without stored AWS keys
- Daily EBS snapshots for the instance root volume

## Layout

- `main.tf`: top-level composition, Cloudflare DNS/proxy record, SSM parameters, and EC2 module wiring
- `modules/ec2`: VPC, subnet, internet gateway, security group, IAM, EC2, snapshots, and Docker bootstrap
- `terraform.tfvars.example`: starter input values

## Apply Flow

1. Copy `terraform.tfvars.example` to `terraform.tfvars`.
2. Replace placeholder values with the real domain, Cloudflare zone/record details, SSH CIDR, key pair, secret values (including the Logfire write token), and GitHub repository/environment if they differ from the defaults.
3. Run `terraform init`.
4. Run `terraform plan`.
5. Run `terraform apply`.
6. Confirm the Cloudflare DNS record is proxied.
7. Copy the `github_actions_role_arn` output into the GitHub `production` environment variable `AWS_ROLE_TO_ASSUME`.
8. Configure the GitHub `production` environment variables listed below, then deploy with the GitHub Actions workflow.

## Runtime

The EC2 security group exposes only:

- `80/tcp` from Cloudflare proxy IP ranges
- `443/tcp` from Cloudflare proxy IP ranges
- `22/tcp` for SSH from `allowed_ssh_cidr_blocks`

Terraform reads Cloudflare's current proxy IP ranges through the Cloudflare provider and uses them in the AWS security group. Caddy serves the React build at `https://<domain>/`, proxies `/api/` and `/admin/` to the Django container, and stores runtime data in the `caddy_data` Docker volume. Postgres data is stored in the `postgres_data` Docker volume.

## App Deployment

GitHub Actions is the only production deployment path. A push to `main` validates the code, builds the web and API images, publishes them to the private ECR repositories, and deploys their immutable digests through SSM. A workflow dispatch can deploy another branch; it resolves that branch to one commit before validation, build, and deployment.

Set these GitHub `production` environment variables:

- `APP_DOMAIN`
- `AWS_REGION` (`us-east-1` by default)
- `AWS_ROLE_TO_ASSUME` (the `github_actions_role_arn` Terraform output)
- `CADDY_ACME_EMAIL`
- Optional runtime values: `OPENAI_MODEL`, `POSTGRES_DB`, `POSTGRES_USER`, and `SSM_PARAMETER_PREFIX`

The EC2 host does not fetch source code or build images. It receives the checked-out Compose configuration and image digests from the workflow, pulls those images from ECR, runs migrations, and starts Docker Compose. ECR lifecycle policies retain only the three newest immutable releases per service.

## GitHub OIDC Deployment Role

Terraform creates an AWS IAM OIDC provider for `token.actions.githubusercontent.com` and a deploy role limited to the configured GitHub repository and Actions environment. With the defaults in this stack, only the subject below can assume the role:

```text
repo:JakubSu/WHOOP:environment:production
```

The role can send SSM Run Command to the provisioned EC2 instance and read command status. It cannot read app secrets directly. Point the GitHub Actions variable `AWS_ROLE_TO_ASSUME` at the `github_actions_role_arn` Terraform output and keep `id-token: write` enabled in the workflow.

## Secret Handling

Terraform creates app parameters under `/<project_name>/<environment>`, including SecureString values for secrets and a String value for the WHOOP OAuth client ID. Django reads required values from SSM at startup when `DEBUG=false`; the deployment bootstrap also reads the Postgres password from SSM so the Postgres container can initialize.

SecureString values are sensitive Terraform variables, but Terraform-managed SSM parameter values can still be present in Terraform state. Keep local state files out of source control and prefer a secured remote backend before using this for long-lived production secrets.

## Container Logs

Terraform creates a CloudWatch Logs group at `/<project_name>/<environment>/docker` and grants the EC2 instance role permission to create log streams and publish events inside that group. Docker Compose uses the `awslogs` logging driver for Caddy, Django API, and Postgres containers.

Apply Terraform before deploying app changes that enable CloudWatch logging. The deployment bootstrap writes `CLOUDWATCH_LOG_GROUP` into the instance `.env` file from the SSM parameter prefix.
