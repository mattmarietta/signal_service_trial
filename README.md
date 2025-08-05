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

## Quick Start

### 1. Clone the repo
git clone https://github.com/vlqv9210/signal_service_trial.git
cd signal_service_trial

### 2. Install dependencies
pip install fastapi uvicorn matplotlib

### 3. Start Logging service
uvicorn api:app --reload --port 8000

### 4. Open dashboard in browser
###    http://127.0.0.1:8000/static/index.html

### 5. In a new terminal, run Integrity Monitor:
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

signal_service_trial/
├── api.py                  # Logging & Visualization FastAPI service
├── logger.py               # Logger class (writes JSONL, calls classifier)
├── classifier.py           # Keyword-based classifier (configurable)
├── logs.jsonl              # Log storage
├── static/                 # Dashboard assets
│   ├── index.html
│   ├── style.css
│   └── script.js
├── integrity_service/      # Signal Integrity Monitor
│   ├── config.yaml         # thresholds & keywords
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── main.py             # FastAPI service with auth, health, anomaly logic
│   ├── models.py           # Pydantic + SQLAlchemy schemas
│   ├── requirements.txt
│   └── integrity.db        # SQLite (auto-generated)
├── requirements.txt        # Combined or root dependencies
└── README.md               # This file

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

