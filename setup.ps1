# ClusterMaster Setup Script
# Automatyczna instalacja i konfiguracja

Write-Host "🚀 ClusterMaster - Setup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Sprawdź Python
Write-Host "📦 Checking Python..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}
$pythonVersion = python --version
Write-Host "✅ $pythonVersion" -ForegroundColor Green

# Sprawdź Node.js
Write-Host "📦 Checking Node.js..." -ForegroundColor Yellow
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}
$nodeVersion = node --version
Write-Host "✅ Node.js $nodeVersion" -ForegroundColor Green

# Sprawdź kubectl
Write-Host "📦 Checking kubectl..." -ForegroundColor Yellow
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ kubectl not found - required for cluster management" -ForegroundColor Yellow
}
else {
    Write-Host "✅ kubectl installed" -ForegroundColor Green
}

# Sprawdź terraform
Write-Host "📦 Checking terraform..." -ForegroundColor Yellow
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ terraform not found - required for EKS clusters" -ForegroundColor Yellow
}
else {
    Write-Host "✅ terraform installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan

# Backend dependencies
Write-Host ""
Write-Host "📦 Installing Python packages..." -ForegroundColor Yellow
Push-Location backend
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

# Frontend dependencies
Write-Host ""
Write-Host "📦 Installing Node.js packages..." -ForegroundColor Yellow
Push-Location frontend
npm install --silent
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location


Write-Host ""
Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run application: .\start.ps1" -ForegroundColor White
Write-Host "  2. Or manually:" -ForegroundColor White
Write-Host "     Backend:  cd backend; python -m uvicorn simple_main:app --reload" -ForegroundColor Gray
Write-Host "     Frontend: cd frontend; npm run dev" -ForegroundColor Gray
Write-Host ""
