# Update .env with WHATSAPP_APP_SECRET and fetch BUSINESS_ACCOUNT_ID from Meta API
# Use script-relative path to avoid Turkish char issues

$envPath = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
Write-Host "ENV path: $envPath" -ForegroundColor Cyan

if (-not (Test-Path $envPath)) {
    Write-Host ".env file not found at $envPath" -ForegroundColor Red
    exit 1
}

# 1. Update WHATSAPP_APP_SECRET
$appSecret = [System.Environment]::GetEnvironmentVariable('WHATSAPP_APP_SECRET', 'Machine')
if ($appSecret) {
    Write-Host "WHATSAPP_APP_SECRET found (length=$($appSecret.Length))" -ForegroundColor Green
    $content = [System.IO.File]::ReadAllText($envPath)
    $content = $content.Replace('WHATSAPP_APP_SECRET=REPLACE_ME', "WHATSAPP_APP_SECRET=$appSecret")
    [System.IO.File]::WriteAllText($envPath, $content)
    Write-Host ".env updated with WHATSAPP_APP_SECRET" -ForegroundColor Green
} else {
    Write-Host "WHATSAPP_APP_SECRET NOT FOUND in env vars" -ForegroundColor Red
}

# 2. Fetch WHATSAPP_BUSINESS_ACCOUNT_ID from Meta Graph API
$phoneId = [System.Environment]::GetEnvironmentVariable('WHATSAPP_PHONE_ID', 'Machine')
$token = [System.Environment]::GetEnvironmentVariable('WHATSAPP_TOKEN', 'Machine')

if ($phoneId -and $token) {
    Write-Host ""
    Write-Host "Fetching WHATSAPP_BUSINESS_ACCOUNT_ID from Meta API..." -ForegroundColor Cyan
    Write-Host "Phone ID: $phoneId" -ForegroundColor Cyan
    try {
        $url = "https://graph.facebook.com/v21.0/${phoneId}?fields=whatsapp_business_account"
        $headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
        $response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get -ErrorAction Stop

        if ($response.whatsapp_business_account -and $response.whatsapp_business_account.id) {
            $businessId = $response.whatsapp_business_account.id
            Write-Host "WHATSAPP_BUSINESS_ACCOUNT_ID: $businessId" -ForegroundColor Green

            # Update .env
            $content = [System.IO.File]::ReadAllText($envPath)
            $content = $content.Replace('WHATSAPP_BUSINESS_ACCOUNT_ID=REPLACE_ME', "WHATSAPP_BUSINESS_ACCOUNT_ID=$businessId")
            [System.IO.File]::WriteAllText($envPath, $content)
            Write-Host ".env updated with WHATSAPP_BUSINESS_ACCOUNT_ID" -ForegroundColor Green
        } else {
            Write-Host "Response:" -ForegroundColor Yellow
            $response | ConvertTo-Json -Depth 3 | Write-Host
        }
    } catch {
        Write-Host "API Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errorBody = $reader.ReadToEnd()
            Write-Host "Error body: $errorBody" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Missing WHATSAPP_PHONE_ID or WHATSAPP_TOKEN" -ForegroundColor Red
}

# 3. Final check
Write-Host ""
Write-Host "=== Final .env check ===" -ForegroundColor Cyan
$finalContent = [System.IO.File]::ReadAllText($envPath)
if ($finalContent.Contains('REPLACE_ME')) {
    Write-Host "Still has REPLACE_ME values:" -ForegroundColor Yellow
    $finalContent -split "`n" | Where-Object { $_ -match 'REPLACE_ME' } | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
} else {
    Write-Host "ALL values are set! Ready for Docker." -ForegroundColor Green
}
