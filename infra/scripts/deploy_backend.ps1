param(
    [Parameter(Mandatory = $true)]
    [string]$InstanceId,

    [Parameter(Mandatory = $true)]
    [string]$AppDomain,

    [Parameter(Mandatory = $true)]
    [string]$AcmeEmail,

    [string]$AwsRegion = "us-east-1",
    [string]$SsmParameterPrefix = "/whoop-ai-coach/prod",
    [string]$PostgresDb = "whoop_ai_coach",
    [string]$PostgresUser = "whoop_ai_coach",
    [string]$OpenAiModel = "gpt-4.1-mini",
    [string]$RepositoryUrl = "https://github.com/JakubSu/WHOOP.git",
    [string]$Branch = "main",
    [string]$AwsProfile
)

$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:AWS_CLI_FILE_ENCODING = "utf-8"

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList
    )

    & $FilePath @ArgumentList

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($ArgumentList -join ' ')"
    }
}

function ConvertTo-BashSingleQuoted {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Value
    )

    return "'" + $Value.Replace("'", "'""'""'") + "'"
}

$bootstrapScript = Join-Path $PSScriptRoot "bootstrap_backend.sh"

if (-not (Test-Path $bootstrapScript)) {
    throw "Bootstrap script not found: $bootstrapScript"
}

$scriptBase64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($bootstrapScript))
$quotedArgs = @(
    (ConvertTo-BashSingleQuoted $AppDomain),
    (ConvertTo-BashSingleQuoted $AcmeEmail),
    (ConvertTo-BashSingleQuoted $AwsRegion),
    (ConvertTo-BashSingleQuoted $SsmParameterPrefix),
    (ConvertTo-BashSingleQuoted $PostgresDb),
    (ConvertTo-BashSingleQuoted $PostgresUser),
    (ConvertTo-BashSingleQuoted $OpenAiModel),
    (ConvertTo-BashSingleQuoted $RepositoryUrl),
    (ConvertTo-BashSingleQuoted $Branch)
) -join " "

$remoteCommand = @'
bash -lc 'set -euo pipefail; script_path="/tmp/bootstrap_backend.sh"; printf '"'"'%s'"'"' '"'"'__SCRIPT_BASE64__'"'"' | base64 -d > "$script_path"; tr -d '"'"'\r'"'"' < "$script_path" > "$script_path.unix"; chmod +x "$script_path.unix"; sudo bash "$script_path.unix" __BOOTSTRAP_ARGS__'
'@
$remoteCommand = $remoteCommand.Replace("__SCRIPT_BASE64__", $scriptBase64).Replace("__BOOTSTRAP_ARGS__", $quotedArgs)

$ssmParametersPath = Join-Path ([System.IO.Path]::GetTempPath()) ("whoop-ssm-command-" + [System.Guid]::NewGuid().ToString() + ".json")
$commandResponsePath = Join-Path ([System.IO.Path]::GetTempPath()) ("whoop-ssm-command-response-" + [System.Guid]::NewGuid().ToString() + ".json")
$invocationPath = Join-Path ([System.IO.Path]::GetTempPath()) ("whoop-ssm-invocation-" + [System.Guid]::NewGuid().ToString() + ".json")

try {
    [System.IO.File]::WriteAllText(
        $ssmParametersPath,
        (@{ commands = @($remoteCommand) } | ConvertTo-Json -Compress),
        [System.Text.UTF8Encoding]::new($false)
    )

    $awsBaseArguments = @()
    if ($AwsProfile) {
        $awsBaseArguments += @("--profile", $AwsProfile)
    }
    $awsBaseArguments += @("--region", $AwsRegion)

    $commandIdArguments = $awsBaseArguments + @(
        "ssm", "send-command",
        "--instance-ids", $InstanceId,
        "--document-name", "AWS-RunShellScript",
        "--comment", "Deploy WHOOP app",
        "--parameters", "file://$ssmParametersPath",
        "--output", "json"
    )

    [System.IO.File]::WriteAllText(
        $commandResponsePath,
        (& aws @commandIdArguments),
        [System.Text.UTF8Encoding]::new($false)
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to start SSM deployment command."
    }
    $commandResponse = Get-Content -Raw -Path $commandResponsePath | ConvertFrom-Json
    $commandId = [string]$commandResponse.Command.CommandId
    if ([string]::IsNullOrWhiteSpace($commandId)) {
        throw "Failed to parse SSM deployment command ID."
    }

    Write-Host "Started SSM command: $commandId"

    $status = ""
    for ($attempt = 1; $attempt -le 120; $attempt++) {
        $statusArguments = $awsBaseArguments + @(
            "ssm", "get-command-invocation",
            "--command-id", $commandId,
            "--instance-id", $InstanceId,
            "--query", "Status",
            "--output", "text"
        )

        $status = (& aws @statusArguments 2>$null).Trim()

        switch ($status) {
            "Success" { break }
            "Pending" { Start-Sleep -Seconds 5 }
            "InProgress" { Start-Sleep -Seconds 5 }
            "Delayed" { Start-Sleep -Seconds 5 }
            "Cancelled" { break }
            "TimedOut" { break }
            "Failed" { break }
            "Cancelling" { break }
            default { Start-Sleep -Seconds 5 }
        }

        if ($status -eq "Success" -or $status -eq "Cancelled" -or $status -eq "TimedOut" -or $status -eq "Failed" -or $status -eq "Cancelling") {
            break
        }

        if ($attempt -eq 120) {
            throw "Timed out waiting for the SSM deployment command to finish."
        }
    }

    $invocationArguments = $awsBaseArguments + @(
        "ssm", "get-command-invocation",
        "--command-id", $commandId,
        "--instance-id", $InstanceId,
        "--output", "json"
    )

    [System.IO.File]::WriteAllText(
        $invocationPath,
        (& aws @invocationArguments),
        [System.Text.UTF8Encoding]::new($false)
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to fetch SSM command invocation details."
    }

    $invocation = Get-Content -Raw -Path $invocationPath | ConvertFrom-Json

    if ($invocation.StandardOutputContent) {
        Write-Host $invocation.StandardOutputContent
    }

    if ($invocation.Status -ne "Success") {
        if ($invocation.StandardErrorContent) {
            Write-Error $invocation.StandardErrorContent
        }
        throw "Deployment failed with SSM status '$($invocation.Status)'."
    }
}
finally {
    if (Test-Path $ssmParametersPath) {
        Remove-Item -LiteralPath $ssmParametersPath -Force
    }

    if (Test-Path $commandResponsePath) {
        Remove-Item -LiteralPath $commandResponsePath -Force
    }

    if (Test-Path $invocationPath) {
        Remove-Item -LiteralPath $invocationPath -Force
    }
}

Write-Host "Application deployed to https://$AppDomain"
