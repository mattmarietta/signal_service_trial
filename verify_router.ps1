# PowerShell version of verify_router.sh
Write-Host "🔍 Checking router status..." -ForegroundColor Cyan

try {
    $status = Invoke-RestMethod -Uri "http://localhost:9000/status"
    Write-Host "Router Status:" -ForegroundColor Yellow
    $status | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Error checking router status: $_" -ForegroundColor Red
}

Write-Host "`n🧾 Retrieving last log entries..." -ForegroundColor Cyan

try {
    $logs = Invoke-RestMethod -Uri "http://localhost:9000/log"
    Write-Host "Log Entries:" -ForegroundColor Yellow
    $logs | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Error retrieving logs: $_" -ForegroundColor Red
}

