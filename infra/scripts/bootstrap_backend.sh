#!/bin/bash
set -euo pipefail

APP_DIR="/opt/whoop-ai-coach"
DEPLOY_LOG_DIR="/var/log/whoop-ai-coach"
DEPLOY_LOG="$DEPLOY_LOG_DIR/deploy.log"

APP_DOMAIN="${1:?App domain is required.}"
CADDY_ACME_EMAIL="${2:?Caddy ACME email is required.}"
AWS_REGION="${3:?AWS region is required.}"
SSM_PARAMETER_PREFIX="${4:?SSM parameter prefix is required.}"
OPENAI_MODEL="${5:-gpt-5.6-luna}"
WEB_IMAGE="${6:?Immutable web image is required.}"
API_IMAGE="${7:?Immutable API image is required.}"
COMPOSE_CONFIG_B64="${8:?Compose configuration is required.}"
RELEASE_SHA="${9:?Release commit SHA is required.}"
COACH_CONFIG_B64="${10:?Coach configuration is required.}"

mkdir -p "$DEPLOY_LOG_DIR"
touch "$DEPLOY_LOG"
chmod 640 "$DEPLOY_LOG"
exec > >(tee -a "$DEPLOY_LOG") 2>&1

exec 9>/var/lock/whoop-ai-coach-deploy.lock
if ! flock -n 9; then
  echo "Another WHOOP AI Coach deployment is already running." >&2
  exit 1
fi

validate_image() {
  local image="$1"
  local service="$2"

  if [[ ! "$image" =~ ^[^/]+/.+@sha256:[0-9a-f]{64}$ ]]; then
    echo "$service image must be an immutable ECR digest reference, received: $image" >&2
    exit 1
  fi
}

validate_image "$WEB_IMAGE" "Web"
validate_image "$API_IMAGE" "API"

echo "[$(date --iso-8601=seconds)] Starting release $RELEASE_SHA."
echo "Web image: $WEB_IMAGE"
echo "API image: $API_IMAGE"

mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/secrets"

read_ssm_secret() {
  local env_name="$1"
  local parameter_name="$2"
  local value
  value="$(aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "${SSM_PARAMETER_PREFIX%/}/$parameter_name" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text)"
  printf -v "$env_name" '%s' "$value"
}

read_ssm_secret SECRET_KEY "django/secret-key"
read_ssm_secret OPENAI_API_KEY "openai/api-key"
read_ssm_secret LOGFIRE_TOKEN "logfire/token"
read_ssm_secret WHOOP_CLIENT_ID "whoop/client-id"
read_ssm_secret WHOOP_CLIENT_SECRET "whoop/client-secret"
read_ssm_secret WHOOP_TOKEN_ENCRYPTION_KEY "whoop/token-encryption-key"
read_ssm_secret POSTGRES_PASSWORD "postgres/password"
printf '%s' "$POSTGRES_PASSWORD" >"$APP_DIR/secrets/postgres_password"
chmod 600 "$APP_DIR/secrets/postgres_password"

compose_tmp="$(mktemp "$APP_DIR/compose.yml.XXXXXX")"
trap 'rm -f "$compose_tmp"' EXIT
printf '%s' "$COMPOSE_CONFIG_B64" | base64 --decode >"$compose_tmp"
mv "$compose_tmp" "$APP_DIR/compose.yml"
trap - EXIT

cat >"$APP_DIR/.env" <<EOF
APP_DOMAIN=${APP_DOMAIN}
CADDY_ACME_EMAIL=${CADDY_ACME_EMAIL}
AWS_REGION=${AWS_REGION}
SSM_PARAMETER_PREFIX=${SSM_PARAMETER_PREFIX%/}
CLOUDWATCH_LOG_GROUP=${SSM_PARAMETER_PREFIX%/}/docker
OPENAI_MODEL=${OPENAI_MODEL}
WEB_IMAGE=${WEB_IMAGE}
API_IMAGE=${API_IMAGE}
EOF
for secret_name in SECRET_KEY OPENAI_API_KEY LOGFIRE_TOKEN WHOOP_CLIENT_ID WHOOP_CLIENT_SECRET WHOOP_TOKEN_ENCRYPTION_KEY POSTGRES_PASSWORD; do
  secret_value="${!secret_name}"
  printf "%s='%s'\n" "$secret_name" "${secret_value//\'/\'\\\'\'}" >>"$APP_DIR/.env"
done
printf '%s' "$COACH_CONFIG_B64" | base64 --decode >>"$APP_DIR/.env"
printf '\n' >>"$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"

cat >"$APP_DIR/release.env" <<EOF
RELEASE_SHA=${RELEASE_SHA}
WEB_IMAGE=${WEB_IMAGE}
API_IMAGE=${API_IMAGE}
DEPLOYED_AT=$(date --iso-8601=seconds)
EOF
chmod 600 "$APP_DIR/release.env"

registry="${WEB_IMAGE%%/*}"
aws ecr get-login-password --region "$AWS_REGION" |
  docker login --username AWS --password-stdin "$registry"

cd "$APP_DIR"
docker compose --env-file .env pull caddy api
echo "[$(date --iso-8601=seconds)] Running database migrations."
docker compose --env-file .env run --rm api python manage.py migrate --noinput
echo "[$(date --iso-8601=seconds)] Starting Docker Compose services."
docker compose --env-file .env up -d --remove-orphans caddy api db

for attempt in $(seq 1 12); do
  if curl --fail --silent --show-error --resolve "${APP_DOMAIN}:443:127.0.0.1" "https://${APP_DOMAIN}/" >/dev/null; then
    echo "[$(date --iso-8601=seconds)] Deployment completed."
    exit 0
  fi
  sleep 5
done

echo "Caddy did not become healthy after deployment." >&2
docker compose --env-file .env ps >&2
exit 1
