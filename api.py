from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import matplotlib
matplotlib.use("Agg")      # force non-interactive backend
import matplotlib.pyplot as plt
import io
import os
import json
import httpx
import logging
from datetime import datetime

from logger import Logger
from classifier import classify_signal

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

logger = Logger("logs.jsonl")
app = FastAPI(title="Signal Service API")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Router integration configuration
ROUTER_URL = os.getenv("ROUTER_URL", "http://localhost:9000/ingest")
INTEGRITY_URL = os.getenv("INTEGRITY_URL", "http://localhost:8001/event")
INTEGRITY_API_KEY = os.getenv("INTEGRITY_API_KEY", "")

log.info(f"Service starting - Router: {ROUTER_URL}, Integrity: {INTEGRITY_URL}")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers"""
    return {
        "status": "ok",
        "service": "signal-logging",
        "version": "1.0.0"
    }

@app.post("/log")
async def log_interaction(data: dict):
    """
    Vy's logging endpoint that:
    1. Classifies sentiment
    2. Writes to logs.jsonl
    3. Optionally calls integrity service
    4. Forwards to router /ingest endpoint
    """
    # 1) Classify sentiment from text
    text = data.get("text") or data.get("payload", {}).get("text") or data.get("user_input", "")
    sentiment = classify_signal(text) if text else "neutral"

    # Prepare record for logging
    rec = data.copy()
    rec["sentiment"] = sentiment

    # Write to logs.jsonl (backwards compatible with existing logger.write)
    # Handle both old format (agent_id, user_id, user_input) and new format (user_id, agent_id, timestamp, payload)
    if "user_input" in rec:
        # Old format
        logger.write(
            agent_id=rec.get("agent_id", "default"),
            user_id=rec.get("user_id", "unknown"),
            user_input=rec.get("user_input", ""),
            detected_signal=sentiment,
            session_id=rec.get("session_id")
        )
    else:
        # New format - write raw JSON to logs.jsonl
        with open("logs.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")

    # 2) Optionally call integrity service
    integrity_ok = True
    integrity_issues = []

    # If integrity URL is configured and API key exists, call it
    if INTEGRITY_URL and INTEGRITY_API_KEY:
        try:
            # Handle timestamp - convert string to datetime if needed for integrity service
            timestamp = rec.get("timestamp")
            if isinstance(timestamp, str):
                # Try parsing ISO format string to datetime for integrity service
                try:
                    timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    timestamp_dt = datetime.now()
            elif timestamp is None:
                timestamp_dt = datetime.now()
            else:
                timestamp_dt = timestamp

            integrity_payload = {
                "user_id": rec.get("user_id") or rec.get("user", ""),
                "agent_id": rec.get("agent_id") or rec.get("context_tag", ""),
                "signal_type": rec.get("signal_type", sentiment),
                "timestamp": timestamp_dt.isoformat(),
                "payload": rec.get("payload", {})
            }
            async with httpx.AsyncClient(timeout=5) as client:
                integrity_response = await client.post(
                    INTEGRITY_URL,
                    json=integrity_payload,
                    headers={"X-API-Key": INTEGRITY_API_KEY}
                )
                if integrity_response.status_code != 200:
                    integrity_issues.append(f"Integrity check failed: {integrity_response.status_code}")
                    log.warning(f"Integrity check failed with status {integrity_response.status_code}")
        except Exception as e:
            # Don't break logging on integrity failure
            log.error(f"Integrity service error: {e}")
            integrity_issues.append(f"Integrity service unreachable: {str(e)}")

    # 3) Build router payload (schema-aligned)
    # Extract values from top-level or payload
    user = rec.get("user_id") or rec.get("user", "")
    session_id = rec.get("session_id", "default")
    timestamp = rec.get("timestamp") or datetime.now().isoformat()
    payload = rec.get("payload", {})

    router_payload = {
        "user": user,
        "session_id": session_id,
        "timestamp": timestamp,
        "text": rec.get("text") or payload.get("text"),
        "hrv": rec.get("hrv") or payload.get("hrv"),
        "ecg": rec.get("ecg") or payload.get("ecg"),
        "gsr": rec.get("gsr") or payload.get("gsr"),
        "fused_score": rec.get("fused_score") or payload.get("fused_score"),
        "context_tag": rec.get("agent_id") or rec.get("context_tag") or "mixed_signal",
        "vy": {
            "integrity_ok": integrity_ok and len(integrity_issues) == 0,
            "issues": integrity_issues,
            "sentiment": sentiment
        }
    }

    # 4) Forward to router
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            await client.post(ROUTER_URL, json=router_payload)
            log.debug(f"Forwarded event to router for user {user}")
        except Exception as e:
            # Don't break logging on forward failure
            log.error(f"Router forward error: {e}")

    log.info(f"Logged event - user: {user}, sentiment: {sentiment}")
    return {"status": "ok", "logged": rec}

@app.get("/logs/{agent_id}/{user_id}")
def get_logs(agent_id: str, user_id: str):
    return logger.read_recent(agent_id, user_id)

@app.get("/summary/{agent_id}/{user_id}")
def get_summary(agent_id: str, user_id: str):
    return logger.summarize_signals(agent_id, user_id)

@app.get("/visualize/{agent_id}/{user_id}")
def visualize(agent_id: str, user_id: str):
    summary = logger.summarize_signals(agent_id, user_id)
    if not summary:
        return JSONResponse({"error": "No data to visualize"}, status_code=404)

    # Create the plot
    fig, ax = plt.subplots()
    ax.bar(summary.keys(), summary.values(), color='skyblue')
    ax.set_title(f"Signal Summary for {agent_id}/{user_id}")
    ax.set_ylabel("Frequency")

    # Save into a BytesIO buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)      # Close the figure to free memory
    buf.seek(0)

    # Stream the PNG image back
    return StreamingResponse(buf, media_type="image/png")