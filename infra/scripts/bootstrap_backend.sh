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

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y awscli docker.io docker-compose-v2 git

systemctl enable --now docker

if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
  rm -rf "$APP_DIR"
  git clone --branch "$BRANCH" --single-branch "$REPOSITORY_URL" "$APP_DIR"
fi

POSTGRES_PASSWORD="$(
  aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "${SSM_PARAMETER_PREFIX%/}/postgres/password" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text
)"

cat >"$APP_DIR/.env" <<EOF
APP_DOMAIN=${APP_DOMAIN}
CADDY_ACME_EMAIL=${CADDY_ACME_EMAIL}
AWS_REGION=${AWS_REGION}
SSM_PARAMETER_PREFIX=${SSM_PARAMETER_PREFIX%/}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
OPENAI_MODEL=${OPENAI_MODEL}
EOF
chmod 600 "$APP_DIR/.env"

cd "$APP_DIR"

docker compose build
docker compose run --rm api python manage.py migrate --noinput
docker compose up -d
