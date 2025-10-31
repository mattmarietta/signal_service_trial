#!/bin/bash

set -e

echo "🔍 Checking router status..."

curl -s http://localhost:9000/status | jq .

echo -e "\n🧾 Retrieving last log entries..."

curl -s http://localhost:9000/log | jq .

