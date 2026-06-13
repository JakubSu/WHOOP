# App Deployment Pipeline

The GitHub Actions app deployment workflow lives in `.github/workflows/deploy-app.yml`.

It deploys application code only. Terraform infrastructure changes are intentionally out of scope.

## Required GitHub Secrets

- Either `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, or an AWS role configured for GitHub OIDC via `AWS_ROLE_TO_ASSUME`.

## Required GitHub Variables

- `EC2_INSTANCE_ID`: EC2 instance ID to target with AWS Systems Manager Run Command.
- `APP_DOMAIN`: public application domain, for example `app.jakubsuran.com`.
- `CADDY_ACME_EMAIL`: email passed to Caddy.

## Optional GitHub Variables

- `AWS_REGION`: defaults to `us-east-1`.
- `AWS_ROLE_TO_ASSUME`: preferred when using GitHub OIDC instead of static AWS keys.
- `SSM_PARAMETER_PREFIX`: defaults to `/whoop-ai-coach/prod`.
- `POSTGRES_DB`: defaults to `whoop_ai_coach`.
- `POSTGRES_USER`: defaults to `whoop_ai_coach`.
- `OPENAI_MODEL`: defaults to `gpt-4.1-mini`.
- `REPOSITORY_URL`: defaults to `https://github.com/JakubSu/WHOOP.git`.

## Infrastructure Prerequisites

- The EC2 instance must be registered in AWS Systems Manager and have the `AmazonSSMManagedInstanceCore` policy attached through its instance role.
- The GitHub deployment identity must be allowed to call `ssm:SendCommand`, `ssm:GetCommandInvocation`, and `ssm:ListCommandInvocations` against the target instance and the `AWS-RunShellScript` document.
- The EC2 IAM role must already allow reading the required SSM parameters.
- The EC2 host must be able to pull `REPOSITORY_URL`.

## What Changed

- The workflow no longer uses SSH, `scp`, host key management, or GitHub-runner SSH ingress.
- GitHub Actions now sends `infra/scripts/bootstrap_backend.sh` to the instance through SSM Run Command and waits for the command to finish before marking the deployment complete.
