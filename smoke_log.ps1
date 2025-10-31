# PowerShell version of smoke_log.sh
Write-Host "🌀 Sending test log to Vy service (port 8000)..." -ForegroundColor Cyan

$body = @{
    user_id = "sara"
    agent_id = "axis"
    timestamp = "2025-10-26T00:00:00Z"
    payload = @{
        text = "checking full pipeline"
        hrv = 42
        ecg = 0.83
        gsr = 0.12
        fused_score = 0.74
    }
} | ConvertTo-Json -Depth 3

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/log" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    Write-Host "✅ Log sent successfully." -ForegroundColor Green
    $response | ConvertTo-Json
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

