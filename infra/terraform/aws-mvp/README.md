# AWS MVP Terraform

This stack provisions the lowest-footprint AWS MVP described in the architecture spec:

- React SPA on AWS Amplify
- Django + SQLite on a single AWS Lightsail instance
- OpenAI key injected into a locked-down backend `.env` file via instance `user_data`

## Layout

- `versions.tf`: Terraform and provider constraints
- `main.tf`: top-level composition
- `modules/amplify`: frontend hosting
- `modules/lightsail`: backend compute, ports, and bootstrap
- `terraform.tfvars.example`: starter input values

## Apply flow

1. Copy `terraform.tfvars.example` to `terraform.tfvars`.
2. Replace the placeholder values with real GitHub, SSH, and OpenAI inputs.
3. Run `terraform init`.
4. Run `terraform plan`.
5. Run `terraform apply`.

## Notes

- The backend module writes `/var/www/backend/.env` with mode `0600` and ownership restricted to the `django` system user.
- The Amplify branch URL is passed into the backend bootstrap so `CORS_ALLOWED_ORIGINS`, `WHOOP_FRONTEND_ALLOWED_ORIGINS`, and `WHOOP_FRONTEND_SUCCESS_URL` stay aligned.
- This stack assumes application deployment onto the Lightsail instance is handled separately from infrastructure provisioning.
