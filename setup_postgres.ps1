# PowerShell script to configure or spin up a dedicated local PostgreSQL database
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   AURA LUXE - PostgreSQL Automated Setup Helper            " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$PG_DIR = "C:\Program Files\PostgreSQL\18\bin"
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$DATA_DIR = Join-Path $PROJECT_ROOT "pgdata"

if (-not (Test-Path "$PG_DIR\psql.exe")) {
    Write-Host "[!] PostgreSQL 18 binaries not found in default path $PG_DIR" -ForegroundColor Red
    exit 1
}

Write-Host "Detected PostgreSQL 18 at: $PG_DIR" -ForegroundColor Green

# Test port 5432 default service
Write-Host "`nTesting connection to existing PostgreSQL service on port 5432..."
$pass = Read-Host -Prompt "Enter your PostgreSQL password for user 'postgres'"
if ([string]::IsNullOrWhiteSpace($pass)) {
    Write-Host "[!] A PostgreSQL password is required for the default cluster." -ForegroundColor Red
    exit 1
}

$env:PGPASSWORD = $pass
$test = & "$PG_DIR\psql.exe" -U postgres -h 127.0.0.1 -p 5432 -c "SELECT 1;" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Connected to PostgreSQL service successfully!" -ForegroundColor Green
    
    # Create database if needed
    & "$PG_DIR\psql.exe" -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE ecommerce_db;" 2>$null
    Write-Host "[OK] Database 'ecommerce_db' is ready." -ForegroundColor Green
    
    # Update .env
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "DB_PASSWORD=.*", "DB_PASSWORD=$pass"
    $envContent = $envContent -replace "USE_POSTGRES=.*", "USE_POSTGRES=True"
    $envContent | Set-Content ".env"
    Write-Host "[OK] Updated .env file with PostgreSQL settings!" -ForegroundColor Green
    
    Write-Host "`nRunning Django migrations on PostgreSQL..." -ForegroundColor Cyan
    python manage.py migrate
    python manage.py seed_store
    Write-Host "[OK] All set! Now running on PostgreSQL." -ForegroundColor Green
} else {
    Write-Host "[!] Could not connect to default PostgreSQL service on port 5432: $test" -ForegroundColor Yellow
    Write-Host "`nWould you like to initialize an isolated local PostgreSQL instance on port 5433 with no password hurdles? (Y/N)" -ForegroundColor Cyan
    $choice = Read-Host
    if ($choice -eq 'Y' -or $choice -eq 'y') {
        if (-not (Test-Path $DATA_DIR)) {
            Write-Host "Initializing new PostgreSQL cluster in $DATA_DIR..." -ForegroundColor Cyan
            & "$PG_DIR\initdb.exe" -D $DATA_DIR -U postgres -A trust -E UTF8
        }
        
        Write-Host "Starting PostgreSQL cluster on port 5433..." -ForegroundColor Cyan
        Start-Process "$PG_DIR\pg_ctl.exe" -ArgumentList "start -D `"$DATA_DIR`" -o `"-p 5433`"" -Wait
        
        Start-Sleep -Seconds 2
        & "$PG_DIR\createdb.exe" -U postgres -p 5433 ecommerce_db 2>$null
        
        # Update .env
        $envContent = Get-Content ".env"
        $envContent = $envContent -replace "DB_PORT=.*", "DB_PORT=5433"
        $envContent = $envContent -replace "DB_PASSWORD=.*", "DB_PASSWORD=postgres"
        $envContent = $envContent -replace "USE_POSTGRES=.*", "USE_POSTGRES=True"
        $envContent | Set-Content ".env"
        
        Write-Host "[OK] Isolated PostgreSQL cluster is running on port 5433!" -ForegroundColor Green
        python manage.py migrate
        python manage.py seed_store
    }
}
