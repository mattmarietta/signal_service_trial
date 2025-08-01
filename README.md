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

## Tech Stack
- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy, Matplotlib  
- **Frontend**: HTML, CSS (glassmorphism), JavaScript, Chart.js  
- **Databases**: JSONL file (logging service), SQLite (integrity service)  

---

## Quick Start

# 1. Clone the repo
git clone https://github.com/vlqv9210/signal_service_trial.git
cd signal_service_trial

# 2. Install dependencies
pip install fastapi uvicorn matplotlib sqlalchemy pydantic

# 3. Start Logging service
uvicorn api:app --reload --port 8000

# 4. Start Integrity Monitor (in a new terminal)
cd integrity_service
uvicorn main:app --reload --port 8001

Logging API runs at http://127.0.0.1:8000

Dashboard: open static/index.html (uses port 8000)

Integrity API runs at http://127.0.0.1:8001


---

## Project Structure

signal_service_trial/
├── api.py              # Logging & Visualization FastAPI service
├── logger.py           # Logger class with classification
├── classifier.py       # Keyword-based signal classifier
├── logs.jsonl          # Generated log storage
├── static/             # Web dashboard (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── script.js
├── integrity_service/
│   ├── models.py       # Pydantic + SQLAlchemy schemas
│   ├── main.py         # Integrity Monitor FastAPI service
│   └── integrity.db    # SQLite database
├── requirements.txt    # Combined dependencies
└── README.md

---

## Design Notes

Structure
- Logging Service separates logging, classification, storage, and visualization logic.
- Integrity Service cleanly layers validation, storage, and anomaly detection.

Scalability
- Swap SQLite → PostgreSQL & Redis for sliding windows.
- Use Kafka/RabbitMQ for event ingestion.
- Deploy multiple FastAPI instances behind a load‐balancer.

Edge Cases
- Clock skew: Normalize timestamps on receipt.
- Out‐of‐order events: Buffer and sort by timestamp.
- DB failures: Implement retries or dead‐letter queues.
- Payload bloat: Reject or truncate large payloads.

### Contributors
Vy Vuong (Author)

