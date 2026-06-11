# AWS MVP Terraform

This stack provisions the AWS MVP described in the architecture spec:

- React SPA on AWS Amplify
- Django + SQLite on a single AWS EC2 instance
- OpenAI key stored in AWS Secrets Manager and fetched on-instance through an IAM role

## Layout

- `versions.tf`: Terraform and provider constraints
- `main.tf`: top-level composition
- `modules/amplify`: frontend hosting
- `modules/ec2`: backend compute, networking, IAM, snapshots, and bootstrap
- `terraform.tfvars.example`: starter input values

## Apply flow

1. Copy `terraform.tfvars.example` to `terraform.tfvars`.
2. Replace the placeholder values with real GitHub and SSH inputs.
3. Export `TF_VAR_openai_api_key` in your shell instead of writing it to disk.
4. Run `terraform init`.
5. Run `terraform plan`.
6. Run `terraform apply`.

## Notes

- The backend module creates a dedicated VPC, subnet, internet gateway, security group, EC2 instance profile, and daily EBS snapshot policy.
- The backend module writes `/var/www/backend/.env` with mode `0600` and ownership restricted to the `django` system user.
- The OpenAI key is stored in AWS Secrets Manager using Terraform's write-only `secret_string_wo` path, so the secret value is not persisted in Terraform state.
- The Amplify branch URL is passed into the backend bootstrap so `CORS_ALLOWED_ORIGINS`, `WHOOP_FRONTEND_ALLOWED_ORIGINS`, and `WHOOP_FRONTEND_SUCCESS_URL` stay aligned.
- This stack assumes application deployment onto the EC2 instance is handled separately from infrastructure provisioning.
