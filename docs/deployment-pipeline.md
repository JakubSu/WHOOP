# App Deployment Pipeline

The GitHub Actions app deployment workflow lives in `.github/workflows/deploy-app.yml`.

It deploys application code only. Terraform infrastructure changes are intentionally out of scope.

## Required GitHub Secrets

- `EC2_SSH_PRIVATE_KEY`: private key used to SSH into the EC2 instance.
- `EC2_SSH_KNOWN_HOSTS`: known-hosts entry for the EC2 host, generated with `ssh-keyscan -H <ec2-host-or-ip>`.

## Required GitHub Variables

- `EC2_HOST`: EC2 public hostname or IP reachable from the GitHub-hosted runner.
- `APP_DOMAIN`: public application domain, for example `app.jakubsuran.com`.
- `CADDY_ACME_EMAIL`: email passed to Caddy.

## Optional GitHub Variables

- `EC2_SSH_USER`: defaults to `ubuntu`.
- `AWS_REGION`: defaults to `us-east-1`.
- `SSM_PARAMETER_PREFIX`: defaults to `/whoop-ai-coach/prod`.
- `POSTGRES_DB`: defaults to `whoop_ai_coach`.
- `POSTGRES_USER`: defaults to `whoop_ai_coach`.
- `OPENAI_MODEL`: defaults to `gpt-4.1-mini`.
- `REPOSITORY_URL`: defaults to `https://github.com/JakubSu/WHOOP.git`.

## Infrastructure Prerequisites

- EC2 SSH ingress must allow GitHub-hosted runner access.
- The EC2 IAM role must already allow reading the required SSM parameters.
- The EC2 host must be able to pull `REPOSITORY_URL`.
