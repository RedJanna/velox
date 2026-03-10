# Fetch WHATSAPP_BUSINESS_ACCOUNT_ID from Meta Graph API
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$phoneId = [System.Environment]::GetEnvironmentVariable('WHATSAPP_PHONE_ID', 'Machine')
$token = [System.Environment]::GetEnvironmentVariable('WHATSAPP_TOKEN', 'Machine')

Write-Host "Phone Number ID: $phoneId"
Write-Host "Token length: $($token.Length)"
Write-Host ""

# Try multiple API versions
$versions = @("v21.0", "v20.0", "v19.0")

foreach ($ver in $versions) {
    Write-Host "Trying API version $ver ..." -ForegroundColor Cyan
    $url = "https://graph.facebook.com/$ver/$phoneId"

    try {
        $params = @{
            Uri = "${url}?fields=whatsapp_business_account&access_token=${token}"
            Method = "Get"
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        $response = Invoke-RestMethod @params

        Write-Host "SUCCESS with $ver" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 5 | Write-Host

        if ($response.whatsapp_business_account) {
            $wabaId = $response.whatsapp_business_account.id
            Write-Host ""
            Write-Host "WHATSAPP_BUSINESS_ACCOUNT_ID = $wabaId" -ForegroundColor Green

            # Update .env
            $envPath = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
            $content = [System.IO.File]::ReadAllText($envPath)
            $content = $content.Replace('WHATSAPP_BUSINESS_ACCOUNT_ID=REPLACE_ME', "WHATSAPP_BUSINESS_ACCOUNT_ID=$wabaId")
            [System.IO.File]::WriteAllText($envPath, $content)
            Write-Host ".env updated!" -ForegroundColor Green
        }
        break
    } catch {
        Write-Host "Failed with $ver : $($_.Exception.Message)" -ForegroundColor Yellow
        if ($_.Exception.Response) {
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $body = $reader.ReadToEnd()
                Write-Host "Error response: $body" -ForegroundColor Yellow
            } catch {}
        }
        Write-Host ""
    }
}
