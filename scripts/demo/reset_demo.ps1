$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not (Test-Path (Join-Path $repoRoot 'docker-compose.yml')) -or -not (Test-Path (Join-Path $repoRoot '.env'))) {
    throw 'This helper only runs from a configured local DataShield Docker demo repository with a root .env.'
}
$dockerContext = (docker context show).Trim()
if ($LASTEXITCODE -ne 0 -or -not $dockerContext) { throw 'Could not identify the active Docker context.' }
$dockerEndpoint = (docker context inspect $dockerContext | ConvertFrom-Json).Endpoints.docker.Host
if ($LASTEXITCODE -ne 0 -or $dockerEndpoint -notmatch '^(npipe|unix)://') {
    throw 'Refusing to reset a remote Docker context. Switch to a local Docker Desktop context first.'
}
$confirmation = Read-Host 'This removes the Docker Compose database volume for this local DataShield demo. Type RESET LOCAL DATASHIELD to continue'
if ($confirmation -cne 'RESET LOCAL DATASHIELD') { throw 'Reset cancelled.' }
if (-not $env:DATASHIELD_DEMO_ADMIN_PASSWORD -or $env:DATASHIELD_DEMO_ADMIN_PASSWORD.Length -lt 12) {
    throw 'Set DATASHIELD_DEMO_ADMIN_PASSWORD to a unique password of at least 12 characters before running this script.'
}
Push-Location $repoRoot
try {
    docker compose down -v
    if ($LASTEXITCODE -ne 0) { throw 'docker compose down failed.' }
    docker compose up --build -d
    if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed.' }
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        try { Invoke-RestMethod 'http://localhost:8001/ready' | Out-Null; $ready = $true; break }
        catch { Start-Sleep -Seconds 3 }
    }
    if (-not $ready) { throw 'Backend did not become ready. Inspect docker compose logs.' }
    docker compose exec -T -e "DATASHIELD_DEMO_ADMIN_PASSWORD=$env:DATASHIELD_DEMO_ADMIN_PASSWORD" backend python scripts/demo/seed_demo.py
    if ($LASTEXITCODE -ne 0) { throw 'Demo seed failed. Inspect docker compose logs backend.' }
    Write-Output 'Local DataShield demo reset, migrated, and seeded.'
}
finally { Pop-Location }
