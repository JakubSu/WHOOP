param(
    [Parameter(Mandatory = $true)]
    [string]$HostName,

    [Parameter(Mandatory = $true)]
    [string]$KeyPath,

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
    [string]$SshUser = "ubuntu"
)

$ErrorActionPreference = "Stop"

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

$bootstrapScript = Join-Path $PSScriptRoot "bootstrap_backend.sh"

if (-not (Test-Path $bootstrapScript)) {
    throw "Bootstrap script not found: $bootstrapScript"
}

Invoke-NativeCommand -FilePath "scp" -ArgumentList @("-i", $KeyPath, $bootstrapScript, "${SshUser}@${HostName}:/tmp/bootstrap_backend.sh")

$remoteCommand = @(
    "chmod +x /tmp/bootstrap_backend.sh",
    "sudo /tmp/bootstrap_backend.sh '$AppDomain' '$AcmeEmail' '$AwsRegion' '$SsmParameterPrefix' '$PostgresDb' '$PostgresUser' '$OpenAiModel' '$RepositoryUrl' '$Branch'"
) -join " && "

Invoke-NativeCommand -FilePath "ssh" -ArgumentList @("-i", $KeyPath, "${SshUser}@${HostName}", $remoteCommand)

Write-Host "Application deployed to https://$AppDomain"
