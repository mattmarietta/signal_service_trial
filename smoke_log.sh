#!/bin/bash

set -e

echo "🌀 Sending test log to Vy service (port 8000)..."

curl -s -X POST http://localhost:8000/log \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"sara",
    "agent_id":"axis",
    "timestamp":"2025-10-26T00:00:00Z",
    "payload":{
      "text":"checking full pipeline",
      "hrv":42,
      "ecg":0.83,
      "gsr":0.12,
      "fused_score":0.74
    }
  }'

echo -e "\n✅ Log sent."

