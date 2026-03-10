# Set WHATSAPP_BUSINESS_ACCOUNT_ID from system env or manual entry
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$envPath = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"

# Check if it exists in Windows env vars
$wabaId = [System.Environment]::GetEnvironmentVariable('WHATSAPP_BUSINESS_ACCOUNT_ID', 'Machine')

if (-not $wabaId) {
    # Try fetching from Meta API
    $token = [System.Environment]::GetEnvironmentVariable('WHATSAPP_TOKEN', 'Machine')
    $phoneId = [System.Environment]::GetEnvironmentVariable('WHATSAPP_PHONE_ID', 'Machine')

    try {
        $url = "https://graph.facebook.com/v21.0/$phoneId`?fields=whatsapp_business_account&access_token=$token"
        $resp = Invoke-RestMethod -Uri $url -Method Get -ErrorAction Stop
        if ($resp.whatsapp_business_account) {
            $wabaId = $resp.whatsapp_business_account.id
        }
    } catch {}
}

if ($wabaId) {
    Write-Host "WHATSAPP_BUSINESS_ACCOUNT_ID: $wabaId" -ForegroundColor Green
    $content = [System.IO.File]::ReadAllText($envPath)
    $content = $content.Replace('WHATSAPP_BUSINESS_ACCOUNT_ID=REPLACE_ME', "WHATSAPP_BUSINESS_ACCOUNT_ID=$wabaId")
    [System.IO.File]::WriteAllText($envPath, $content)
    Write-Host ".env updated!" -ForegroundColor Green
} else {
    # Not critical for Docker testing - set empty
    Write-Host "WABA ID not found. Setting empty (not critical for local testing)" -ForegroundColor Yellow
    $content = [System.IO.File]::ReadAllText($envPath)
    $content = $content.Replace('WHATSAPP_BUSINESS_ACCOUNT_ID=REPLACE_ME', "WHATSAPP_BUSINESS_ACCOUNT_ID=")
    [System.IO.File]::WriteAllText($envPath, $content)
    Write-Host ".env updated with empty WABA ID" -ForegroundColor Yellow
}

# Final check
Write-Host ""
$finalContent = [System.IO.File]::ReadAllText($envPath)
if ($finalContent.Contains('REPLACE_ME')) {
    Write-Host "Still has REPLACE_ME values!" -ForegroundColor Red
} else {
    Write-Host "ALL values set! .env is ready for Docker." -ForegroundColor Green
}
