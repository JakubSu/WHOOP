#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  infra/scripts/deploy_backend_macos.sh \
    --instance-id i-0123456789abcdef0 \
    --app-domain app.example.com \
    --acme-email admin@example.com

Options:
  --instance-id VALUE            Required EC2 instance ID.
  --app-domain VALUE             Required public app domain.
  --acme-email VALUE             Required Caddy ACME email.
  --aws-region VALUE             AWS region. Default: us-east-1.
  --ssm-parameter-prefix VALUE   SSM parameter prefix. Default: /whoop-ai-coach/prod.
  --postgres-db VALUE            Postgres database name. Default: whoop_ai_coach.
  --postgres-user VALUE          Postgres username. Default: whoop_ai_coach.
  --openai-model VALUE           OpenAI model name. Default: gpt-4.1-mini.
  --repository-url VALUE         Repository URL the EC2 host should pull.
                                  Default: https://github.com/JakubSu/WHOOP.git.
  --branch VALUE                 Git branch to deploy. Default: main.
  --aws-profile VALUE            Optional AWS CLI profile.
  -h, --help                     Show this help.
EOF
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

print_ssm_invocation_output() {
  local label="$1"
  local query="$2"

  echo "===== $label ====="
  aws "${aws_base_args[@]}" ssm get-command-invocation \
    --command-id "$command_id" \
    --instance-id "$instance_id" \
    --query "$query" \
    --output text || true
  echo "===== end $label ====="
}

print_ssm_invocation_metadata() {
  echo "===== SSM invocation metadata ====="
  aws "${aws_base_args[@]}" ssm get-command-invocation \
    --command-id "$command_id" \
    --instance-id "$instance_id" \
    --query '{Status:Status,StatusDetails:StatusDetails,ResponseCode:ResponseCode,ExecutionStartDateTime:ExecutionStartDateTime,ExecutionEndDateTime:ExecutionEndDateTime,PluginName:PluginName}' \
    --output table || true
  echo "===== end SSM invocation metadata ====="
}

instance_id=""
app_domain=""
acme_email=""
aws_region="us-east-1"
ssm_parameter_prefix="/whoop-ai-coach/prod"
postgres_db="whoop_ai_coach"
postgres_user="whoop_ai_coach"
openai_model="gpt-4.1-mini"
repository_url="https://github.com/JakubSu/WHOOP.git"
branch="main"
aws_profile=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --instance-id)
      instance_id="${2:?--instance-id requires a value}"
      shift 2
      ;;
    --app-domain)
      app_domain="${2:?--app-domain requires a value}"
      shift 2
      ;;
    --acme-email)
      acme_email="${2:?--acme-email requires a value}"
      shift 2
      ;;
    --aws-region)
      aws_region="${2:?--aws-region requires a value}"
      shift 2
      ;;
    --ssm-parameter-prefix)
      ssm_parameter_prefix="${2:?--ssm-parameter-prefix requires a value}"
      shift 2
      ;;
    --postgres-db)
      postgres_db="${2:?--postgres-db requires a value}"
      shift 2
      ;;
    --postgres-user)
      postgres_user="${2:?--postgres-user requires a value}"
      shift 2
      ;;
    --openai-model)
      openai_model="${2:?--openai-model requires a value}"
      shift 2
      ;;
    --repository-url)
      repository_url="${2:?--repository-url requires a value}"
      shift 2
      ;;
    --branch)
      branch="${2:?--branch requires a value}"
      shift 2
      ;;
    --aws-profile)
      aws_profile="${2:?--aws-profile requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ -z "$instance_id" ] || [ -z "$app_domain" ] || [ -z "$acme_email" ]; then
  echo "--instance-id, --app-domain, and --acme-email are required." >&2
  usage >&2
  exit 1
fi

require_command aws
require_command base64
require_command python3

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bootstrap_script="$script_dir/bootstrap_backend.sh"

if [ ! -f "$bootstrap_script" ]; then
  echo "Bootstrap script not found: $bootstrap_script" >&2
  exit 1
fi

ssm_parameters_path="$(mktemp "${TMPDIR:-/tmp}/whoop-ssm-command.XXXXXX.json")"
send_response_path="$(mktemp "${TMPDIR:-/tmp}/whoop-ssm-send-response.XXXXXX.json")"

cleanup() {
  rm -f "$ssm_parameters_path" "$send_response_path"
}
trap cleanup EXIT

script_b64="$(base64 < "$bootstrap_script" | tr -d '\n')"

APP_DOMAIN="$app_domain" \
CADDY_ACME_EMAIL="$acme_email" \
AWS_REGION="$aws_region" \
SSM_PARAMETER_PREFIX="$ssm_parameter_prefix" \
POSTGRES_DB="$postgres_db" \
POSTGRES_USER="$postgres_user" \
OPENAI_MODEL="$openai_model" \
REPOSITORY_URL="$repository_url" \
TARGET_BRANCH="$branch" \
SCRIPT_B64="$script_b64" \
python3 - <<'PY' > "$ssm_parameters_path"
import json
import os
import shlex

args = [
    os.environ["APP_DOMAIN"],
    os.environ["CADDY_ACME_EMAIL"],
    os.environ["AWS_REGION"],
    os.environ["SSM_PARAMETER_PREFIX"],
    os.environ["POSTGRES_DB"],
    os.environ["POSTGRES_USER"],
    os.environ["OPENAI_MODEL"],
    os.environ["REPOSITORY_URL"],
    os.environ["TARGET_BRANCH"],
]

quoted_args = " ".join(shlex.quote(arg) for arg in args)
inner = (
    "set -euo pipefail; "
    'script_path="/tmp/bootstrap_backend.sh"; '
    f"printf '%s' {shlex.quote(os.environ['SCRIPT_B64'])} | base64 -d > \"$script_path\"; "
    "tr -d '\\r' < \"$script_path\" > \"$script_path.unix\"; "
    "chmod +x \"$script_path.unix\"; "
    f"sudo bash \"$script_path.unix\" {quoted_args}"
)

print(json.dumps({"commands": [f"bash -lc {shlex.quote(inner)}"]}))
PY

aws_base_args=()
if [ -n "$aws_profile" ]; then
  aws_base_args+=(--profile "$aws_profile")
fi
aws_base_args+=(--region "$aws_region")

echo "Starting SSM deployment command."
if ! aws "${aws_base_args[@]}" ssm send-command \
  --instance-ids "$instance_id" \
  --document-name "AWS-RunShellScript" \
  --comment "Deploy WHOOP app" \
  --parameters "file://$ssm_parameters_path" \
  --output json > "$send_response_path"; then
  echo "Failed to start SSM deployment command." >&2
  cat "$send_response_path" >&2 || true
  exit 1
fi

command_id="$(python3 - "$send_response_path" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    payload = json.load(fh)

print(payload["Command"]["CommandId"])
PY
)"

if [ -z "$command_id" ]; then
  echo "Failed to parse SSM deployment command ID." >&2
  exit 1
fi

echo "Started SSM command: $command_id"

status=""
for attempt in $(seq 1 120); do
  status="$(aws "${aws_base_args[@]}" ssm get-command-invocation \
    --command-id "$command_id" \
    --instance-id "$instance_id" \
    --query Status \
    --output text 2>/dev/null || true)"

  case "$status" in
    Success)
      break
      ;;
    Pending|InProgress|Delayed|"")
      sleep 5
      ;;
    Cancelled|TimedOut|Failed|Cancelling)
      echo "SSM command failed with status: $status" >&2
      print_ssm_invocation_metadata
      print_ssm_invocation_output "SSM standard output" StandardOutputContent
      print_ssm_invocation_output "SSM standard error" StandardErrorContent
      exit 1
      ;;
    *)
      sleep 5
      ;;
  esac

  if [ "$attempt" -eq 120 ]; then
    echo "Timed out waiting for SSM deployment command to finish." >&2
    print_ssm_invocation_metadata
    print_ssm_invocation_output "SSM standard output" StandardOutputContent
    print_ssm_invocation_output "SSM standard error" StandardErrorContent
    exit 1
  fi
done

print_ssm_invocation_output "SSM standard output" StandardOutputContent

final_status="$(aws "${aws_base_args[@]}" ssm get-command-invocation \
  --command-id "$command_id" \
  --instance-id "$instance_id" \
  --query Status \
  --output text)"

if [ "$final_status" != "Success" ]; then
  print_ssm_invocation_metadata
  print_ssm_invocation_output "SSM standard error" StandardErrorContent
  echo "Deployment failed with SSM status '$final_status'." >&2
  exit 1
fi

echo "Application deployed to https://$app_domain"
