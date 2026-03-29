from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from app import config

Base = declarative_base()
engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    api_key = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String)
    plan = Column(String, default="free")  # free, pro, enterprise
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class InferenceLog(Base):
    __tablename__ = "inference_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model = Column(String)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    energy_used = Column(Float)
    energy_remaining = Column(Float)
    mode_used = Column(String)
    entropy_observed = Column(Float)
    cost_baseline = Column(Float)
    cost_actual = Column(Float)

class ControllerState(Base):
    __tablename__ = "controller_states"
    id = Column(String, primary_key=True)  # conversation_id
    user_id = Column(String, index=True)
    energy_remaining = Column(Float)
    error_debt = Column(Float)
    last_mode = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)
