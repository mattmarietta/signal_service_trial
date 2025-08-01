from datetime import datetime
from collections import deque, defaultdict
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Pydantic model for validation
class SignalEvent(BaseModel):
    user_id: str
    agent_id: str
    signal_type: str
    timestamp: datetime
    payload: dict = Field(default_factory=dict)

# 2. SQLAlchemy ORM setup
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

# 3. SQLite engine & session
engine = create_engine("sqlite:///integrity.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# 4. Create tables
Base.metadata.create_all(bind=engine)

# 5. In-memory sliding windows: user_id → deque of timestamps
windows = defaultdict(lambda: deque())
