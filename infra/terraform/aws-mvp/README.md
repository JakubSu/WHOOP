# AWS MVP Terraform

This stack provisions the single-instance AWS deployment:

- React UI, Django API, Caddy, and Postgres on one EC2 instance through Docker Compose
- HTTPS through Cloudflare proxy mode in front of Caddy
- Cloudflare proxied app `A` record
- Production secrets in SSM Parameter Store
- EC2 IAM role scoped to the app SSM parameters
- GitHub Actions OIDC role for SSM-based app deployments without stored AWS keys
- Daily EBS snapshots for the instance root volume

## Layout

- `main.tf`: top-level composition, Cloudflare DNS/proxy record, SSM parameters, and EC2 module wiring
- `modules/ec2`: VPC, subnet, internet gateway, security group, IAM, EC2, snapshots, and Docker bootstrap
- `terraform.tfvars.example`: starter input values

## Apply Flow

1. Copy `terraform.tfvars.example` to `terraform.tfvars`.
2. Replace placeholder values with the real domain, Cloudflare zone/record details, SSH CIDR, key pair, secret values, and GitHub repository/environment if they differ from the defaults.
3. Run `terraform init`.
4. Run `terraform plan`.
5. Run `terraform apply`.
6. Confirm the Cloudflare DNS record is proxied.
7. Copy the `github_actions_role_arn` output into the GitHub `production` environment variable `AWS_ROLE_TO_ASSUME`.
8. Deploy the app with `infra/scripts/deploy_backend.ps1` or the GitHub Actions workflow.

## Runtime

The EC2 security group exposes only:

- `80/tcp` from Cloudflare proxy IP ranges
- `443/tcp` from Cloudflare proxy IP ranges
- `22/tcp` for SSH from `allowed_ssh_cidr_blocks`

Terraform reads Cloudflare's current proxy IP ranges through the Cloudflare provider and uses them in the AWS security group. Caddy serves the React build at `https://<domain>/`, proxies `/api/` and `/admin/` to the Django container, and stores runtime data in the `caddy_data` Docker volume. Postgres data is stored in the `postgres_data` Docker volume.

## App Deployment

`infra/scripts/deploy_backend.ps1` sends an SSM Run Command to the EC2 instance and asks the host to pull the application code from Git. By default it pulls `https://github.com/JakubSu/WHOOP.git` on `main`.

Example:

```powershell
.\infra\scripts\deploy_backend.ps1 `
  -InstanceId i-0123456789abcdef0 `
  -AppDomain app.example.com `
  -AcmeEmail admin@example.com
```

For a private repository, either pass a repository URL the EC2 host can access with `-RepositoryUrl`, or preconfigure repo access on the instance before running the deploy script.

## GitHub OIDC Deployment Role

Terraform creates an AWS IAM OIDC provider for `token.actions.githubusercontent.com` and a deploy role limited to the configured GitHub repository and Actions environment. With the defaults in this stack, only the subject below can assume the role:

```text
repo:JakubSu/WHOOP:environment:production
```

The role can send SSM Run Command to the provisioned EC2 instance and read command status. It cannot read app secrets directly. Point the GitHub Actions variable `AWS_ROLE_TO_ASSUME` at the `github_actions_role_arn` Terraform output and keep `id-token: write` enabled in the workflow.

## Secret Handling

Terraform creates SecureString parameters under `/<project_name>/<environment>`. Django reads required secrets from SSM at startup when `DEBUG=false`; the deployment bootstrap also reads the Postgres password from SSM so the Postgres container can initialize.

SecureString values are sensitive Terraform variables, but Terraform-managed SSM parameter values can still be present in Terraform state. Keep local state files out of source control and prefer a secured remote backend before using this for long-lived production secrets.
