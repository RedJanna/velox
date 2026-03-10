$envPath = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
$secret = [System.Environment]::GetEnvironmentVariable('WHATSAPP_APP_SECRET_V', 'Machine')
if (-not $secret) { Write-Error "WHATSAPP_APP_SECRET_V not found"; exit 1 }
$content = [System.IO.File]::ReadAllText($envPath)
$content = $content -replace 'WHATSAPP_APP_SECRET=.*', "WHATSAPP_APP_SECRET=$secret"
[System.IO.File]::WriteAllText($envPath, $content)
Write-Host "Updated WHATSAPP_APP_SECRET ($($secret.Length) chars)"
