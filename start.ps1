# ClusterMaster Start Script
# Uruchamia backend i frontend w osobnych oknach PowerShell

Write-Host "🚀 Starting ClusterMaster..." -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Sprawdź czy dependencies są zainstalowane
if (-not (Test-Path "$scriptPath\backend\__pycache__") -or -not (Test-Path "$scriptPath\frontend\node_modules")) {
    Write-Host "⚠️  Dependencies not installed. Running setup first..." -ForegroundColor Yellow
    & "$scriptPath\setup.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Setup failed. Please fix errors and try again." -ForegroundColor Red
        exit 1
    }
}

Write-Host "🔧 Starting Backend..." -ForegroundColor Yellow
$backendPath = Join-Path $scriptPath "backend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; Write-Host '🔧 Backend Server' -ForegroundColor Cyan; Write-Host 'Starting uvicorn...' -ForegroundColor Yellow; python -m uvicorn simple_main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 2

Write-Host "🎨 Starting Frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path $scriptPath "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; Write-Host '🎨 Frontend Dev Server' -ForegroundColor Cyan; Write-Host 'Starting Vite...' -ForegroundColor Yellow; npm run dev"

Write-Host ""
Write-Host "✅ ClusterMaster is starting!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Services:" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Two PowerShell windows will open - one for backend, one for frontend" -ForegroundColor Gray
Write-Host "    Close those windows to stop the servers" -ForegroundColor Gray
Write-Host ""
