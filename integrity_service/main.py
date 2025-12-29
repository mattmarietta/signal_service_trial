import os
import logging
from datetime import timedelta, datetime
import yaml
import redis
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from models import Event, Anomaly, SessionLocal, Base, engine
from dotenv import load_dotenv

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


load_dotenv()

# ─── 1. Load and validate configuration ────────────────────────────────────────
try:
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)

    # Validate required configuration keys
    required_keys = ["database", "redis", "thresholds"]
    for key in required_keys:
        if key not in cfg:
            raise ValueError(f"Missing required config key: {key}")

    DB_URL       = cfg["database"]["url"]
    REDIS_URL    = cfg["redis"]["url"]
    WEBHOOK_URL  = cfg.get("webhook", {}).get("url", "")
    THRESHOLDS   = cfg["thresholds"]

    logger.info(f"Configuration loaded successfully from config.yaml")
    logger.info(f"Database: {DB_URL}")
    logger.info(f"Redis: {REDIS_URL}")
    logger.info(f"Webhook configured: {bool(WEBHOOK_URL)}")

except FileNotFoundError:
    logger.error("config.yaml not found in current directory")
    raise
except yaml.YAMLError as e:
    logger.error(f"Failed to parse config.yaml: {e}")
    raise
except Exception as e:
    logger.error(f"Configuration error: {e}")
    raise

# ─── 2. Initialize Redis with connection validation ────────────────────────────
try:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()  # Test connection on startup
    logger.info("Redis connection successful")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis at {REDIS_URL}: {e}")
    raise
except Exception as e:
    logger.error(f"Redis initialization error: {e}")
    raise

# ─── 3. FastAPI app & Auth stub ────────────────────────────────────────────────
app = FastAPI(title="Signal Integrity Monitor")

def api_key_auth(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")

# ─── 4. Database session dependency ───────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── 5. Retry decorator for commits ────────────────────────────────────────────
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def commit_with_retry(db: Session):
    db.commit()

# ─── 6. Pydantic model for incoming events ────────────────────────────────────
class SignalEvent(BaseModel):
    user_id: str
    agent_id: str
    signal_type: str
    timestamp: datetime
    payload: dict = {}

# ─── 7. Health check endpoint ─────────────────────────────────────────────────
@app.get("/health")
def health():
    try:
        # Use SQLAlchemy 2.x compatible approach
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        r.ping()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhealthy: {e}")
    return {"status": "ok"}

# ─── 8. Ingest endpoint with anomaly logic ────────────────────────────────────
@app.post("/event", dependencies=[Depends(api_key_auth)])
def ingest(evt: SignalEvent, db: Session = Depends(get_db)):
    # 1. Store event
    db_evt = Event(**evt.dict())
    db.add(db_evt)
    commit_with_retry(db)

    # 2. Redis sliding window
    key = f"window:{evt.user_id}"
    now_ts = evt.timestamp.timestamp()
    r.zadd(key, {now_ts: now_ts})
    r.expire(key, 60)  # auto-expire window after 60s of inactivity

    # 3. Purge older than 5s
    cutoff = (evt.timestamp - timedelta(seconds=5)).timestamp()
    r.zremrangebyscore(key, 0, cutoff)

    # 4. Count and threshold per signal_type
    count = r.zcard(key)
    thresh = THRESHOLDS.get(evt.signal_type, THRESHOLDS["default"])
    if count > thresh:
        # determine severity
        severity = "critical" if count > thresh * 1.5 else "warning"
        # find window start
        earliest_ts = float(r.zrange(key, 0, 0)[0])
        window_start = datetime.fromtimestamp(earliest_ts)

        # 5. Record anomaly
        anomaly = Anomaly(
            user_id=evt.user_id,
            detected_at=evt.timestamp,
            count=count,
            window_start=window_start,
            severity=severity,
            rule=f"{evt.signal_type}:{thresh}"
        )
        db.add(anomaly)
        commit_with_retry(db)

        # 6. Log anomaly detection
        logger.warning(
            f"Anomaly detected - user: {evt.user_id}, type: {evt.signal_type}, "
            f"count: {count}, severity: {severity}, threshold: {thresh}"
        )

        # 7. Webhook alert for critical
        if severity == "critical" and WEBHOOK_URL:
            try:
                requests.post(
                    WEBHOOK_URL,
                    json={
                        "user_id": evt.user_id,
                        "signal_type": evt.signal_type,
                        "count": count,
                        "severity": severity,
                        "detected_at": evt.timestamp.isoformat()
                    },
                    timeout=1
                )
                logger.info(f"Critical anomaly webhook sent for user {evt.user_id}")
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")

    return {"status": "ingested"}

# ─── 9. Retrieve anomalies ────────────────────────────────────────────────────
@app.get("/anomalies/{user_id}", dependencies=[Depends(api_key_auth)])
def get_anomalies(user_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(Anomaly)
          .filter(Anomaly.user_id == user_id)
          .order_by(Anomaly.detected_at.desc())
          .all()
    )
    return [r.as_dict() for r in records]