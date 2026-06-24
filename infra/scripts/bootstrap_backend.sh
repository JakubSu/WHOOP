#!/bin/bash
set -euo pipefail

APP_DIR="/opt/whoop-ai-coach"

APP_DOMAIN="${1:?App domain is required.}"
CADDY_ACME_EMAIL="${2:?Caddy ACME email is required.}"
AWS_REGION="${3:?AWS region is required.}"
SSM_PARAMETER_PREFIX="${4:?SSM parameter prefix is required.}"
POSTGRES_DB="${5:-whoop_ai_coach}"
POSTGRES_USER="${6:-whoop_ai_coach}"
OPENAI_MODEL="${7:-gpt-4.1-mini}"
REPOSITORY_URL="${8:?Repository URL is required.}"
BRANCH="${9:-main}"
DEPLOY_LOG_DIR="/var/log/whoop-ai-coach"
DEPLOY_LOG="$DEPLOY_LOG_DIR/deploy.log"

export DEBIAN_FRONTEND=noninteractive

mkdir -p "$DEPLOY_LOG_DIR"
touch "$DEPLOY_LOG"
chmod 640 "$DEPLOY_LOG"
exec > >(tee -a "$DEPLOY_LOG") 2>&1

scm_url_for_logs() {
  sed -E 's#(https?://)[^/@]+@#\1***@#' <<<"$1"
}

run_scm_command() {
  local description="$1"
  shift

  local output_file
  output_file="$(mktemp)"

  echo "[$(date --iso-8601=seconds)] SCM: $description."
  if "$@" >"$output_file" 2>&1; then
    cat "$output_file"
    rm -f "$output_file"
    return 0
  fi

  local exit_code=$?
  echo "SCM command failed while trying to $description." >&2
  echo "Exit code: $exit_code" >&2
  echo "Repository: $(scm_url_for_logs "$REPOSITORY_URL")" >&2
  echo "Branch: $BRANCH" >&2
  echo "Command output:" >&2
  cat "$output_file" >&2
  rm -f "$output_file"
  return "$exit_code"
}

echo "[$(date --iso-8601=seconds)] Starting WHOOP AI Coach deployment."
echo "Deploying branch '$BRANCH' from '$(scm_url_for_logs "$REPOSITORY_URL")'."

apt-get update
apt-get install -y curl docker.io docker-compose-v2 git unzip

if ! command -v aws >/dev/null 2>&1; then
  tmp_dir="$(mktemp -d)"
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "$tmp_dir/awscliv2.zip"
  unzip -q "$tmp_dir/awscliv2.zip" -d "$tmp_dir"
  "$tmp_dir/aws/install" --update
  rm -rf "$tmp_dir"
fi

systemctl enable --now docker

run_scm_command "verify repository access and branch existence" \
  git ls-remote --exit-code --heads "$REPOSITORY_URL" "$BRANCH"

if [ -d "$APP_DIR/.git" ]; then
  run_scm_command "fetch branch '$BRANCH' into existing checkout" \
    git -C "$APP_DIR" fetch origin "$BRANCH"
  run_scm_command "reset existing checkout to origin/$BRANCH" \
    git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
  rm -rf "$APP_DIR"
  run_scm_command "clone branch '$BRANCH' into $APP_DIR" \
    git clone --branch "$BRANCH" --single-branch "$REPOSITORY_URL" "$APP_DIR"
fi

mkdir -p "$APP_DIR/secrets"
aws ssm get-parameter \
  --region "$AWS_REGION" \
  --name "${SSM_PARAMETER_PREFIX%/}/postgres/password" \
  --with-decryption \
  --query 'Parameter.Value' \
  --output text >"$APP_DIR/secrets/postgres_password"
chmod 600 "$APP_DIR/secrets/postgres_password"

cat >"$APP_DIR/.env" <<EOF
APP_DOMAIN=${APP_DOMAIN}
CADDY_ACME_EMAIL=${CADDY_ACME_EMAIL}
AWS_REGION=${AWS_REGION}
SSM_PARAMETER_PREFIX=${SSM_PARAMETER_PREFIX%/}
CLOUDWATCH_LOG_GROUP=${SSM_PARAMETER_PREFIX%/}/docker
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
OPENAI_MODEL=${OPENAI_MODEL}
EOF
chmod 600 "$APP_DIR/.env"

cd "$APP_DIR"

echo "[$(date --iso-8601=seconds)] Building Docker images."
docker compose build
echo "[$(date --iso-8601=seconds)] Running database migrations."
docker compose run --rm api python manage.py migrate --noinput
echo "[$(date --iso-8601=seconds)] Starting Docker Compose services."
docker compose up -d
echo "[$(date --iso-8601=seconds)] Deployment completed."
