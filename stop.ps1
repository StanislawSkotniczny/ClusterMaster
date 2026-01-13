# ClusterMaster Stop Script
# Zatrzymuje wszystkie procesy ClusterMaster

Write-Host "🛑 Stopping ClusterMaster..." -ForegroundColor Cyan
Write-Host ""

# Zatrzymaj procesy Python (uvicorn)
Write-Host "Stopping backend processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*python*" -and $_.CommandLine -like "*uvicorn*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Zatrzymaj procesy Node (Vite)
Write-Host "Stopping frontend processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*node*" -and $_.CommandLine -like "*vite*"} | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "✅ ClusterMaster stopped" -ForegroundColor Green
