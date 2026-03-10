# Check if WhatsApp token is valid and find Business Account ID
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$token = [System.Environment]::GetEnvironmentVariable('WHATSAPP_TOKEN', 'Machine')
$phoneId = [System.Environment]::GetEnvironmentVariable('WHATSAPP_PHONE_ID', 'Machine')

# Test 1: Check token validity
Write-Host "=== Test 1: Token validity ===" -ForegroundColor Cyan
try {
    $debugUrl = "https://graph.facebook.com/debug_token?input_token=$token&access_token=$token"
    $debugResp = Invoke-RestMethod -Uri $debugUrl -Method Get -ErrorAction Stop
    Write-Host "Token valid: $($debugResp.data.is_valid)" -ForegroundColor Green
    Write-Host "App ID: $($debugResp.data.app_id)" -ForegroundColor Green
    Write-Host "Type: $($debugResp.data.type)" -ForegroundColor Green
    if ($debugResp.data.expires_at -and $debugResp.data.expires_at -ne 0) {
        $expiry = [DateTimeOffset]::FromUnixTimeSeconds($debugResp.data.expires_at).DateTime
        Write-Host "Expires: $expiry" -ForegroundColor Yellow
    } else {
        Write-Host "Expires: Never (system user token)" -ForegroundColor Green
    }
    if ($debugResp.data.error) {
        Write-Host "Error: $($debugResp.data.error.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "Token debug failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Get phone number details
Write-Host ""
Write-Host "=== Test 2: Phone number lookup ===" -ForegroundColor Cyan
try {
    $phoneUrl = "https://graph.facebook.com/v21.0/$phoneId`?access_token=$token"
    $phoneResp = Invoke-RestMethod -Uri $phoneUrl -Method Get -ErrorAction Stop
    Write-Host "Phone details:" -ForegroundColor Green
    $phoneResp | ConvertTo-Json -Depth 3 | Write-Host
} catch {
    Write-Host "Phone lookup failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Direct WABA lookup
Write-Host ""
Write-Host "=== Test 3: WABA lookup ===" -ForegroundColor Cyan
try {
    $wabaUrl = "https://graph.facebook.com/v21.0/$phoneId/whatsapp_business_account?access_token=$token"
    $wabaResp = Invoke-RestMethod -Uri $wabaUrl -Method Get -ErrorAction Stop
    Write-Host "WABA:" -ForegroundColor Green
    $wabaResp | ConvertTo-Json -Depth 3 | Write-Host
} catch {
    Write-Host "WABA lookup failed: $($_.Exception.Message)" -ForegroundColor Red
}
