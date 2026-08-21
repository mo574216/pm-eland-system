[CmdletBinding()]
param(
    [string]$ComposeFile = "infrastructure/compose/docker-compose.dev.yml",
    [int]$FrontendPort = 5173,
    [int]$BackendPort = 8000,
    [string]$DockerExecutable = "docker"
)

$ErrorActionPreference = "Stop"

$backendResponse = Invoke-RestMethod -Uri "http://localhost:$BackendPort/health/ready"
if (-not $backendResponse.success -or $backendResponse.data.checks.database -ne "ok") {
    throw "Backend readiness did not confirm PostgreSQL connectivity."
}

$frontendResponse = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$FrontendPort/"
if ($frontendResponse.StatusCode -ne 200) {
    throw "Frontend did not return HTTP 200."
}

$corsResponse = Invoke-WebRequest `
    -UseBasicParsing `
    -Method Options `
    -Uri "http://localhost:$BackendPort/health/live" `
    -Headers @{
        Origin = "http://localhost:$FrontendPort"
        "Access-Control-Request-Method" = "GET"
    }
if ($corsResponse.Headers["Access-Control-Allow-Origin"] -ne "http://localhost:$FrontendPort") {
    throw "Backend CORS does not allow the local frontend origin."
}

& $DockerExecutable compose -f $ComposeFile exec -T backend python -c "import socket; [(lambda connection: connection.close())(socket.create_connection((host, port), timeout=3)) for host, port in [('postgres', 5432), ('minio', 9000), ('redis', 6379)]]"
if ($LASTEXITCODE -ne 0) {
    throw "Backend container could not reach one or more required services."
}

& $DockerExecutable compose -f $ComposeFile exec -T backend alembic current
if ($LASTEXITCODE -ne 0) {
    throw "Alembic migration verification failed."
}

Write-Host "Local Compose smoke tests passed."
