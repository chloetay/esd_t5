import os
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Request
# Import CORS middleware
from fastapi.middleware.cors import CORSMiddleware # <--- ADDED IMPORT
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Password123!@pgdb:5432/transactionlogs")

# Create the SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------------------
# Database Model
# -------------------------------
class TransactionLog(Base):
    __tablename__ = "transaction_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(100), nullable=False)
    stripe_payment_id = Column(String(100), nullable=True)
    wallet_id = Column(String(100), nullable=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), nullable=False)
    transaction_type = Column(String(50), default="top_up")
    payment_method_type = Column(String(50), nullable=True)
    log_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

# -------------------------------
# Pydantic Schemas
# -------------------------------
class TransactionLogCreate(BaseModel):
    payment_id: str
    stripe_payment_id: Optional[str] = None
    wallet_id: Optional[str] = None
    amount: int
    currency: str = "usd"
    status: str
    transaction_type: Optional[str] = "top_up"
    payment_method_type: Optional[str] = None
    log_metadata: Optional[str] = None # Changed from Optional[Dict] to allow JSON string or dict
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TransactionLogResponse(BaseModel):
    id: str
    payment_id: str
    amount: int
    currency: str
    status: str
    transaction_type: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True # Deprecated, use from_attributes=True in Pydantic v2
        # from_attributes = True # For Pydantic v2

# -------------------------------
# Database Dependency
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

# Helper function to convert DB model to UI-compatible format
def convert_to_ui_format(log: TransactionLog) -> Dict[str, Any]:
    # Try to parse log_metadata to extract additional info if available
    metadata = {}
    try:
        if log.log_metadata:
            metadata = json.loads(log.log_metadata)
    except (json.JSONDecodeError, TypeError):
        pass # Keep metadata empty if parsing fails

    return {
        "id": log.id,
        "payment_id": log.payment_id,
        "amount": log.amount,
        "currency": log.currency,
        "status": log.status,
        "transaction_type": log.transaction_type or "top_up",
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "completed_at": log.completed_at.isoformat() if log.completed_at else None
        # You could optionally add parsed metadata here if needed by UI
        # "metadata": metadata
    }

# Initialize FastAPI app
app = FastAPI(title="Transaction Logs Microservice")

# --- ADDED CORS MIDDLEWARE --- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. For production, restrict this to your frontend's origin.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# --- END OF ADDED CORS MIDDLEWARE --- #


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    logger.info(f"Request: {request.method} {path}")

    try:
        response = await call_next(request)
        logger.info(f"Response: {request.method} {path} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error: {request.method} {path} - {str(e)}")
        raise

# -------------------------------
# API Endpoints
# -------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "transaction-logs"}

# --- Modified create_log_record to handle metadata better ---
def create_log_record(log_data: TransactionLogCreate, db: Session):
    """Helper function to create a log record"""
    log_metadata_str = None
    if isinstance(log_data.log_metadata, dict):
        try:
            log_metadata_str = json.dumps(log_data.log_metadata)
        except TypeError:
            logger.warning(f"Could not serialize metadata for payment {log_data.payment_id}")
    elif isinstance(log_data.log_metadata, str):
         # Assume it's already a JSON string or simple string
        log_metadata_str = log_data.log_metadata

    created_at = log_data.created_at or datetime.utcnow()

    db_log = TransactionLog(
        payment_id=log_data.payment_id,
        stripe_payment_id=log_data.stripe_payment_id,
        wallet_id=log_data.wallet_id,
        amount=log_data.amount,
        currency=log_data.currency.lower() if log_data.currency else 'usd', # Ensure lowercase
        status=log_data.status,
        transaction_type=log_data.transaction_type or "top_up",
        payment_method_type=log_data.payment_method_type,
        log_metadata=log_metadata_str,
        created_at=created_at,
        completed_at=log_data.completed_at
    )

    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return convert_to_ui_format(db_log)
# --- End of modified create_log_record ---

@app.post("/api/logs") # Endpoint for direct calls from payment service
def create_direct_log(
    log_data: TransactionLogCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Creating log via direct endpoint: {log_data.payment_id}")
    return create_log_record(log_data, db)

# Note: Removed the duplicate POST / endpoint as /api/logs is preferred for clarity
# If Kong needs POST /, ensure Kong config routes `/api/transaction-logs` POST -> `/api/logs` or update service path in kong.yml

@app.get("/") # Corresponds to Kong's /api/transaction-logs (if strip_path=true) OR direct /
def list_transaction_logs(db: Session = Depends(get_db)):
    """List all transaction logs"""
    logger.info("Listing all transaction logs")
    logs = db.query(TransactionLog).order_by(TransactionLog.created_at.desc()).all()
    return [convert_to_ui_format(log) for log in logs]

@app.get("/{log_id}") # Corresponds to Kong's /api/transaction-logs/{id} (if strip_path=true) OR direct /{id}
def get_transaction_log(log_id: str, db: Session = Depends(get_db)):
    """Retrieve a single transaction log by ID"""
    logger.info(f"Getting log by ID: {log_id}")
    db_log = db.query(TransactionLog).filter(TransactionLog.id == log_id).first()
    if not db_log:
        raise HTTPException(status_code=404, detail="Transaction log not found")
    return convert_to_ui_format(db_log)

@app.get("/user/{wallet_id}") # Primary endpoint for direct UI calls
def list_wallet_transaction_logs(wallet_id: str, db: Session = Depends(get_db)):
    """Retrieve logs for a specific wallet ID"""
    logger.info(f"Fetching logs for wallet_id (string): {wallet_id}")

    try:
        # Ensure the session is clean before querying
        db.commit()

        query = db.query(TransactionLog).filter(TransactionLog.wallet_id == str(wallet_id))
        logs = query.order_by(TransactionLog.created_at.desc()).all()

        # # Optional: Attempt fallback with integer if string match fails and it's a digit
        # if not logs and wallet_id.isdigit():
        #     logger.info(f"Retrying log fetch for wallet_id (integer): {wallet_id}")
        #     query_int = db.query(TransactionLog).filter(TransactionLog.wallet_id == int(wallet_id))
        #     logs = query_int.order_by(TransactionLog.created_at.desc()).all()

        logger.info(f"Found {len(logs)} logs for wallet_id {wallet_id}")
        return [convert_to_ui_format(log) for log in logs]

    except Exception as e:
        logger.error(f"Error fetching logs for wallet {wallet_id}: {str(e)}")
        db.rollback() # Rollback in case of error during query/processing
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")


# Keep the full path endpoint for potential Kong compatibility if strip_path=false on gateway
@app.get("/api/transaction-logs/user/{wallet_id}")
def list_wallet_transaction_logs_full_path(wallet_id: str, db: Session = Depends(get_db)):
    """Retrieve logs for a specific wallet ID using the full path"""
    logger.info(f"Full path endpoint fetching logs for wallet_id: {wallet_id}")
    # Simply calls the main function to avoid code duplication
    return list_wallet_transaction_logs(wallet_id=wallet_id, db=db)


@app.get("/debug/logs")
def debug_logs(db: Session = Depends(get_db)):
    """Debugging endpoint to view all logs"""
    logger.info("Debug logs endpoint called")
    logs = db.query(TransactionLog).order_by(TransactionLog.created_at.desc()).all()
    results = [convert_to_ui_format(log) for log in logs]

    # Also include raw DB records for debugging if needed
    raw_data = []
    for log in logs:
         raw_data.append({col.name: getattr(log, col.name) for col in log.__table__.columns})

    return {
        "count": len(results),
        "db_url_status": "Connected" if engine else "Not Connected",
        "formatted_logs": results,
        # "raw_logs": raw_data # Uncomment if needed
    }

# Create the database tables if they don't exist
# Note: In production, consider using Alembic for migrations
Base.metadata.create_all(bind=engine)
logger.info("Database tables checked/created.")

# Run the app using uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server for Transaction Logs Service...")
    # Match host/port/reload with docker-compose command if applicable
    uvicorn.run("app:app", host="0.0.0.0", port=8005, reload=True)