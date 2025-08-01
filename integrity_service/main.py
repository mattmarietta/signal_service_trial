from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from collections import defaultdict, deque

from models import SignalEvent, Event, Anomaly, SessionLocal, windows

app = FastAPI(title="Signal Integrity Monitor")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/event")
def ingest(event: SignalEvent, db: Session = Depends(get_db)):
    """
    1. Validate via Pydantic (automatically).
    2. Store valid event.
    3. Update sliding window and flag anomaly if >10 events in 5s.
    """
    # Store event
    db_evt = Event(**event.dict())
    db.add(db_evt)
    db.commit()

    # Anomaly detection
    now = event.timestamp
    window = windows[event.user_id]
    window.append(now)

    # Purge timestamps older than 5 seconds
    cutoff = now - timedelta(seconds=5)
    while window and window[0] < cutoff:
        window.popleft()

    if len(window) > 10:
        anomaly = Anomaly(
            user_id=event.user_id,
            detected_at=now,
            count=len(window),
            window_start=window[0]
        )
        db.add(anomaly)
        db.commit()

    return {"status": "ingested"}

@app.get("/anomalies/{user_id}")
def get_anomalies(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieve all anomalies for a given user_id, most recent first.
    """
    records = (
        db.query(Anomaly)
          .filter(Anomaly.user_id == user_id)
          .order_by(Anomaly.detected_at.desc())
          .all()
    )
    return [
        {
            "detected_at": a.detected_at,
            "count": a.count,
            "window_start": a.window_start
        }
        for a in records
    ]
