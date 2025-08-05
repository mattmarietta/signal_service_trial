from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ─── 1. Pydantic model for validation ──────────────────────────────────────────
class SignalEvent(BaseModel):
    user_id: str
    agent_id: str
    signal_type: str
    timestamp: datetime
    payload: dict = Field(default_factory=dict)

# ─── 2. SQLAlchemy ORM setup ──────────────────────────────────────────────────
Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    agent_id = Column(String)
    signal_type = Column(String)
    timestamp = Column(DateTime, index=True)
    payload = Column(JSON)

class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    detected_at = Column(DateTime, index=True)
    count = Column(Integer)
    window_start = Column(DateTime)
    severity = Column(String, default="warning")
    rule = Column(String)  # e.g. "stressed:8"

    def as_dict(self):
        return {
            "user_id": self.user_id,
            "detected_at": self.detected_at.isoformat(),
            "count": self.count,
            "window_start": self.window_start.isoformat(),
            "severity": self.severity,
            "rule": self.rule,
        }

# ─── 3. SQLite engine & session ───────────────────────────────────────────────
from pathlib import Path
import yaml

# Load DB URL from config.yaml
try:
    cfg = yaml.safe_load(Path("config.yaml").read_text())
    db_url = cfg["database"]["url"]
except Exception:
    db_url = "sqlite:///integrity.db"

engine = create_engine(db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# ─── 4. Create tables ─────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)
