# Signal Microservices Suite

A collection of two lightweight Python microservices for handling and analyzing AI-agent signal data:

1. **Signal Logging & Visualization** – Logs interactions, auto-classifies sentiments, and provides a web dashboard.  
2. **Signal Integrity Monitor** – Validates incoming events, stores them, and flags rapid–fire anomalies.

---

## Service 1: Logging & Visualization

### Inspiration  
Quickly understand user sentiment in AI conversations by logging and visualizing “signals” (positive, neutral, stressed, uncertain).

### What It Does  
- **Logs** user–agent interactions to `logs.jsonl`  
- **Classifies** each entry via keyword‐based NLP  
- **API Endpoints**:  
  - `POST /log` → record interaction  
  - `GET /logs/{agent_id}/{user_id}` → last 10 entries  
  - `GET /summary/{agent_id}/{user_id}` → JSON frequency  
  - `GET /visualize/{agent_id}/{user_id}` → PNG bar chart  
- **Dashboard** (`static/index.html`): Chart.js bar chart + recent‐logs table with emojis & color highlights  

---

## Service 2: Signal Integrity Monitor

### Task  
Ensure signal data integrity by validating schemas, storing events, and flagging anomalies when a user emits >10 events in 5 seconds.

### What It Does  
- **Accepts** `POST /event` with JSON fields: `user_id`, `agent_id`, `signal_type`, `timestamp`, `payload`  
- **Validates** via Pydantic; invalid → HTTP 422  
- **Stores** all events in SQLite (`events` table)  
- **Anomaly Detection**: in-memory sliding window per `user_id`; if >10 events in 5 s, logs to `anomalies` table  
- **Endpoints**:  
  - `POST /event` → ingest & flag anomalies  
  - `GET /anomalies/{user_id}` → list anomalies for that user  

---

### Tech Stack
- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy, Matplotlib  
- **Frontend**: HTML, CSS (glassmorphism), JavaScript, Chart.js  
- **Datastores**:  
  - JSONL file (`logs.jsonl`) for logging service  
  - SQLite (default) or Postgres for integrity service  
  - Redis for sliding window state  

---

## Quick Start (Local Setup for now)

### 1. Clone the repo
git clone https://github.com/vlqv9210/signal_service_trial.git
cd signal_service_trial

### 2. Install dependencies
pip install fastapi uvicorn matplotlib


### 3. Configuration (Required for Local Run)
**A. Configure Integrity Service (Port 8001):**
The `config.yaml` file must be updated to use hardcoded, local URLs.
- **File:** `integrity_service/config.yaml`
- **Changes:**

```yaml
# BEFORE
database:
  url: ${DATABASE_URL:-sqlite:///integrity.db}
redis:
  url: ${REDIS_URL:-redis://localhost:6379/0}
webhook:
  url: ${ALERT_WEBHOOK_URL:-}

# AFTER
database:
  url: sqlite:///integrity.db
redis:
  url: redis://localhost:6379/0
webhook:
  url: ""
```

**B. Configure Logging Dashboard (Port 8000):**
The api.py file must be updated to serve the static folder.
 - **File:** api.py (in the root folder)
- **Changes:** Python
```python
# Add these imports at the top
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
# ... other imports

# Add this line right after 'app = FastAPI()'
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### 4. Start Logging service
uvicorn api:app --reload --port 8000

### 5. Open dashboard in browser
###  http://127.0.0.1:8000/static/index.html

### 6. In a new terminal, run Integrity Monitor:
cd integrity_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

Logging API runs at http://127.0.0.1:8000
Dashboard: open static/index.html (uses port 8000)
Integrity API runs at http://127.0.0.1:8001

---

## Docker (Integrity Monitor)
cd integrity_service
docker-compose up --build

Integrity service on http://localhost:8001, Redis on 6379


---

## Project Structure
<img width="611" height="392" alt="Screenshot 2025-08-05 at 1 30 14 AM" src="https://github.com/user-attachments/assets/66835dfc-bc77-48f2-90ee-bda6b7313eff" />

---

## Design Notes

Overall Structure
- Logging Service handles sentiment logging, classification, and dashboard visualization.
- Integrity Service handles schema validation, durable storage, anomaly detection, and alerting.

Scalability
- Databases: Swap SQLite → Postgres, use connection pooling.
- State: Move sliding windows to Redis for multi-instance consistency.
- Ingestion: Buffer via Kafka/RabbitMQ, process with background workers.
- Deployment: Containerize with Docker, run multiple FastAPI instances behind a load-balancer.

Edge Cases
- Clock Skew: Use server receipt timestamp or normalize client times.
- Out-of-order Events: Buffer and reorder by timestamp or process in arrival order.
- DB Failures: Retry writes and push to a dead-letter queue on persistent failure.
- Large Payloads: Enforce maximum JSON size via Pydantic or API gateway.
- Memory Growth: Redis TTL on sliding-window keys or expire in-memory structures after inactivity.

### Contributors
Vy Vuong (Author)
Maintainer: Matt <October 2025> (ownership transfer from Vy)

---

## Integration Notes (Oct 2025)

This service has been integrated with the **Signal-Router-Service** (Matt, Oct 2025).

- All logs and validated events are now automatically forwarded to the router endpoint at:

  `http://localhost:9000/ingest`

- The router handles encrypted, recursive storage of all signal history.
- Ownership: **Matt**

### Configuration

Create a `.env` file in the root directory with:
Make your api key anything you wish, would be replaced in a different system with something more complex. 

```bash
# Router Integration Configuration
ROUTER_URL=http://localhost:9000/ingest

# Integrity Service Configuration (optional)
INTEGRITY_URL=http://localhost:8001/event
INTEGRITY_API_KEY=your_api_key_here
```

### Schema Mapping

The `/log` endpoint accepts Vy's format and transforms it to the router's expected schema:

**Vy Format:**
```json
{
  "user_id": "string",
  "agent_id": "string",
  "timestamp": "ISO-8601",
  "payload": {
    "text": "optional utterance",
    "hrv": 42,
    "ecg": 0.83,
    "gsr": 0.12,
    "fused_score": 0.74
  }
}
```

**Router Format (automatically mapped):**
```json
{
  "user": "string",
  "session_id": "string",
  "timestamp": "ISO-8601",
  "text": "optional utterance",
  "hrv": 42,
  "ecg": 0.83,
  "gsr": 0.12,
  "fused_score": 0.74,
  "context_tag": "string",
  "vy": {
    "integrity_ok": true,
    "issues": [],
    "sentiment": "neutral"
  }
}
```

**Field Mappings:**
- `user_id` → `user`
- `agent_id` → `context_tag` (or `vy.agent_id`)
- `payload.hrv/ecg/gsr/text/fused_score` → flattened to top-level fields
- Integrity result → `vy.integrity_ok` + `vy.issues`
- Sentiment label from logging → `vy.sentiment`

### Integration Flow

1. **Logging Service** (`/log` on port 8000):
   - Classifies sentiment from text
   - Writes to `logs.jsonl`
   - Optionally calls Integrity Service
   - Forwards to Router Service

2. **Integrity Service** (`/event` on port 8001, optional):
   - Validates event schema
   - Detects anomalies
   - Returns integrity status

3. **Router Service** (`/ingest` on port 9000):
   - Receives transformed payloads
   - Stores encrypted history
   - Provides observability endpoints

### Upstream Services

- **Vy Logging Service**: Port 8000
- **Vy Integrity Service**: Port 8001
- **Signal Router Service**: Port 9000 (Matt's router)

### Testing the Integration

Use the provided helper scripts to test the end-to-end flow:

**Bash/Linux/Mac:**
```bash
chmod +x smoke_log.sh verify_router.sh
./smoke_log.sh      # Send test log to Vy service → router
./verify_router.sh   # Check router status and logs
```

**PowerShell (Windows):**
```powershell
.\smoke_log.ps1      # Send test log to Vy service → router
.\verify_router.ps1   # Check router status and logs
```

### Expected Flow

1. Run Vy's services (8000 + 8001)
2. Run Matt's router (9000)
3. Execute `smoke_log.sh` (or `smoke_log.ps1`) → creates a new log entry and forwards to router
4. Execute `verify_router.sh` (or `verify_router.ps1`) → returns updated router status and encrypted log confirmation