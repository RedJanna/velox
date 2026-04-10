# Generate .env file from Windows system environment variables
# This script reads Machine-level env vars and writes .env without exposing values

$envFile = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"

# Read all needed env vars
$OPENAI_API_KEY = [System.Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'Machine')
$ELEKTRA_API_BASE_URL = [System.Environment]::GetEnvironmentVariable('ELEKTRA_API_BASE_URL', 'Machine')
$ELEKTRA_BOOKING = [System.Environment]::GetEnvironmentVariable('Elektra_Booking', 'Machine')
$ELEKTRA_HOTEL_ID = [System.Environment]::GetEnvironmentVariable('ELEKTRA_HOTEL_ID', 'Machine')
$ELEKTRA_GENERIC_API_BASE_URL = [System.Environment]::GetEnvironmentVariable('ELEKTRA_GENERIC_API_BASE_URL', 'Machine')
$ELEKTRA_GENERIC_LOGIN_TOKEN = [System.Environment]::GetEnvironmentVariable('ELEKTRA_GENERIC_LOGIN_TOKEN', 'Machine')
$ELEKTRA_GENERIC_TENANT = [System.Environment]::GetEnvironmentVariable('ELEKTRA_GENERIC_TENANT', 'Machine')
$ELEKTRA_GENERIC_USERCODE = [System.Environment]::GetEnvironmentVariable('ELEKTRA_GENERIC_USERCODE', 'Machine')
$ELEKTRA_GENERIC_PASSWORD = [System.Environment]::GetEnvironmentVariable('ELEKTRA_GENERIC_PASSWORD', 'Machine')
$WHATSAPP_PHONE_ID = [System.Environment]::GetEnvironmentVariable('WHATSAPP_PHONE_ID', 'Machine')
$WHATSAPP_TOKEN = [System.Environment]::GetEnvironmentVariable('WHATSAPP_TOKEN', 'Machine')
$WHATSAPP_VERIFY_TOKEN = [System.Environment]::GetEnvironmentVariable('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'Machine')
$ADMIN_PHONE = [System.Environment]::GetEnvironmentVariable('ADMIN_PHONE', 'Machine')

# Extract Elektra API key (part after $ in Elektra_Booking)
$ELEKTRA_API_KEY = ""
if ($ELEKTRA_BOOKING -and $ELEKTRA_BOOKING.Contains('$')) {
    $ELEKTRA_API_KEY = $ELEKTRA_BOOKING.Split('$')[1]
}

# Generate strong random secrets
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$APP_SECRET = [Convert]::ToBase64String($bytes)
$rng.GetBytes($bytes)
$JWT_SECRET = [Convert]::ToBase64String($bytes)
$rng.GetBytes($bytes)
$WEBHOOK_SECRET = [Convert]::ToBase64String($bytes)

# Report status (without showing values)
Write-Host "=== Environment Variable Status ===" -ForegroundColor Cyan
$checkVars = @{
    'OPENAI_API_KEY' = $OPENAI_API_KEY
    'ELEKTRA_API_BASE_URL' = $ELEKTRA_API_BASE_URL
    'ELEKTRA_API_KEY (from Elektra_Booking)' = $ELEKTRA_API_KEY
    'ELEKTRA_HOTEL_ID' = $ELEKTRA_HOTEL_ID
    'ELEKTRA_GENERIC_API_BASE_URL' = $ELEKTRA_GENERIC_API_BASE_URL
    'ELEKTRA_GENERIC_LOGIN_TOKEN' = $ELEKTRA_GENERIC_LOGIN_TOKEN
    'ELEKTRA_GENERIC_TENANT' = $ELEKTRA_GENERIC_TENANT
    'ELEKTRA_GENERIC_USERCODE' = $ELEKTRA_GENERIC_USERCODE
    'ELEKTRA_GENERIC_PASSWORD' = $ELEKTRA_GENERIC_PASSWORD
    'WHATSAPP_PHONE_NUMBER_ID' = $WHATSAPP_PHONE_ID
    'WHATSAPP_ACCESS_TOKEN' = $WHATSAPP_TOKEN
    'WHATSAPP_VERIFY_TOKEN' = $WHATSAPP_VERIFY_TOKEN
    'ADMIN_PHONE' = $ADMIN_PHONE
}

$allFound = $true
foreach ($key in $checkVars.Keys | Sort-Object) {
    if ($checkVars[$key]) {
        Write-Host "  OK : $key (length=$($checkVars[$key].Length))" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $key" -ForegroundColor Red
        $allFound = $false
    }
}

# Variables we cannot get from system
Write-Host ""
Write-Host "=== STILL MISSING (manual input needed) ===" -ForegroundColor Yellow
Write-Host "  WHATSAPP_APP_SECRET        - Meta Developers > App Dashboard > Settings > Basic" -ForegroundColor Yellow
Write-Host "  WHATSAPP_BUSINESS_ACCOUNT_ID - Meta Business Manager > WhatsApp settings" -ForegroundColor Yellow

# Generate .env file
$envContent = @"
# ============================================================
# Velox (NexlumeAI) Environment Variables
# Auto-generated from system environment variables
# ============================================================

# --- Application ---
APP_ENV=development
APP_DEBUG=true
APP_PORT=8001
APP_HOST=0.0.0.0
APP_LOG_LEVEL=DEBUG
APP_SECRET_KEY=$APP_SECRET

# --- Database (PostgreSQL) ---
DB_HOST=db
DB_PORT=5432
DB_NAME=velox
DB_USER=velox
DB_PASSWORD=VeloxDB2026!
DB_POOL_MIN=5
DB_POOL_MAX=20

# --- Redis ---
REDIS_URL=redis://redis:6379/0
REDIS_SESSION_TTL_SECONDS=1800
REDIS_RATE_LIMIT_TTL_SECONDS=60

# --- OpenAI ---
OPENAI_API_KEY=$OPENAI_API_KEY
OPENAI_MODEL=gpt-4o
OPENAI_FALLBACK_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2048
OPENAI_TEMPERATURE=0.3

# --- Meta WhatsApp Business API ---
WHATSAPP_API_VERSION=v21.0
WHATSAPP_API_BASE_URL=https://graph.facebook.com
WHATSAPP_PHONE_NUMBER_ID=$WHATSAPP_PHONE_ID
WHATSAPP_BUSINESS_ACCOUNT_ID=REPLACE_ME
WHATSAPP_ACCESS_TOKEN=$WHATSAPP_TOKEN
WHATSAPP_VERIFY_TOKEN=$WHATSAPP_VERIFY_TOKEN
WHATSAPP_APP_SECRET=REPLACE_ME

# --- Elektraweb PMS ---
ELEKTRA_API_BASE_URL=$ELEKTRA_API_BASE_URL
ELEKTRA_API_KEY=$ELEKTRA_API_KEY
ELEKTRA_HOTEL_ID=$ELEKTRA_HOTEL_ID
ELEKTRA_GENERIC_API_BASE_URL=$ELEKTRA_GENERIC_API_BASE_URL
ELEKTRA_GENERIC_LOGIN_TOKEN=$ELEKTRA_GENERIC_LOGIN_TOKEN
ELEKTRA_GENERIC_TENANT=$ELEKTRA_GENERIC_TENANT
ELEKTRA_GENERIC_USERCODE=$ELEKTRA_GENERIC_USERCODE
ELEKTRA_GENERIC_PASSWORD=$ELEKTRA_GENERIC_PASSWORD

# --- Admin Panel ---
ADMIN_JWT_SECRET=$JWT_SECRET
ADMIN_JWT_ALGORITHM=HS256
ADMIN_JWT_EXPIRE_MINUTES=60
ADMIN_WEBHOOK_SECRET=$WEBHOOK_SECRET
ADMIN_PHONE=$ADMIN_PHONE

# --- Rate Limiting ---
RATE_LIMIT_PER_PHONE_PER_MINUTE=30
RATE_LIMIT_PER_PHONE_PER_HOUR=200
RATE_LIMIT_WEBHOOK_PER_MINUTE=100

# --- Hotel Config ---
HOTEL_PROFILES_DIR=data/hotel_profiles
ESCALATION_MATRIX_PATH=data/escalation_matrix.yaml
TEMPLATES_DIR=data/templates
SCENARIOS_DIR=data/scenarios
"@

$envContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline
Write-Host ""
Write-Host "=== .env file written to: $envFile ===" -ForegroundColor Green
Write-Host "NOTE: You still need to replace WHATSAPP_APP_SECRET and WHATSAPP_BUSINESS_ACCOUNT_ID" -ForegroundColor Yellow
