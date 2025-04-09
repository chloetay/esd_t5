import json
import logging
import uuid
import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import stripe

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# API Gateway Configuration
API_GATEWAY_BASE_URL = os.getenv("API_GATEWAY_URL", "http://kong:8000")
TRANSACTION_LOG_ENDPOINT = f"http://transaction-logs-service:8005"
# Fallback direct endpoint in case API gateway fails
DIRECT_TRANSACTION_LOG_ENDPOINT = os.getenv("TRANSACTION_LOGS_URL", "http://transaction-logs-service:8005/api/logs")
PAYMENT_STATUS_ENDPOINT = f"{API_GATEWAY_BASE_URL}/api/payments/status"

# Set Stripe API key from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# In-memory payment tracking (for session duration only)
payment_records = {}

# Pydantic models for API requests and responses
class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str
    wallet_id: Optional[str] = None
    wallet_password: Optional[str] = None  # Add wallet_password field
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PaymentResponse(BaseModel):
    client_secret: str
    payment_id: str

class TransactionLogData(BaseModel):
    payment_id: str
    stripe_payment_id: str
    wallet_id: Optional[str]
    amount: int
    currency: str
    status: str
    transaction_type: str = "top_up"
    payment_method_type: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str
    payment_id: str

class PaymentRecord:
    """Simple in-memory payment record class"""
    def __init__(self, id, stripe_payment_id, amount, currency, status, wallet_id=None, payment_metadata=None):
        self.id = id
        self.stripe_payment_id = stripe_payment_id
        self.amount = amount
        self.currency = currency
        self.status = status
        self.wallet_id = wallet_id
        self.payment_metadata = payment_metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.payment_method_type = None
        self.webhook_received_at = None
        self.stripe_webhook_received = False

    def update_status(self, status):
        self.status = status
        self.updated_at = datetime.utcnow()

    def mark_webhook_received(self):
        self.stripe_webhook_received = True
        self.webhook_received_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "stripe_payment_id": self.stripe_payment_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "wallet_id": self.wallet_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "payment_method_type": self.payment_method_type,
            "webhook_received_at": self.webhook_received_at,
            "stripe_webhook_received": self.stripe_webhook_received,
            "payment_metadata": self.payment_metadata
        }

# Gateway Service Functions
def notify_payment_status(payment_record):
    """
    Notify the API Gateway about payment status changes.
    Also ensures transaction is logged.
    """
    success = False
    
    try:
        payload = {
            "payment_id": payment_record.id,
            "stripe_payment_id": payment_record.stripe_payment_id,
            "status": payment_record.status,
            "wallet_id": payment_record.wallet_id,
            "amount": payment_record.amount,
            "currency": payment_record.currency,
            "updated_at": payment_record.updated_at.isoformat(),
            "metadata": payment_record.payment_metadata
        }
        
        try:
            response = requests.post(
                PAYMENT_STATUS_ENDPOINT, 
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully notified API Gateway for payment {payment_record.id}")
                success = True
            else:
                logger.error(f"Failed to notify API Gateway: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to API Gateway failed: {str(e)}")
        
        # Always log the transaction, regardless of API Gateway status
        transaction_logged = send_transaction_log(payment_record)
        
        # Return True if either API Gateway notification or transaction logging succeeded
        return success or transaction_logged
        
    except Exception as e:
        logger.error(f"Error in payment status notification: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Try transaction logging as a fallback
        return send_transaction_log(payment_record)

def send_transaction_log(payment_record):
    """
    Send transaction data to API Gateway for logging.
    """
    try:
        # Create a dict with all values properly serialized
        log_data = {
            "payment_id": payment_record.id,
            "stripe_payment_id": payment_record.stripe_payment_id,
            "wallet_id": payment_record.wallet_id,
            "amount": payment_record.amount,
            "currency": payment_record.currency,
            "status": payment_record.status,
            "transaction_type": "top_up",
            "payment_method_type": payment_record.payment_method_type,
            "created_at": payment_record.created_at.isoformat(),
            "completed_at": payment_record.webhook_received_at.isoformat() if payment_record.webhook_received_at else payment_record.updated_at.isoformat(),
            "metadata": payment_record.payment_metadata
        }
        
        # Try the API Gateway first
        try:
            logger.info(f"Sending transaction log to API Gateway: {TRANSACTION_LOG_ENDPOINT}")
            response = requests.post(
                TRANSACTION_LOG_ENDPOINT, 
                json=log_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent transaction log for payment {payment_record.id} to API Gateway")
                return True
            else:
                logger.warning(f"API Gateway transaction log failed: {response.status_code} - {response.text}")
                # Fall through to try direct endpoint
        except requests.exceptions.RequestException as e:
            logger.warning(f"API Gateway transaction log request failed: {str(e)}")
            # Fall through to try direct endpoint
            
        # Try direct connection to transaction logs service
        try:
            logger.info(f"Trying direct connection to transaction logs service: {DIRECT_TRANSACTION_LOG_ENDPOINT}")
            
            # Adapt the data format for direct transaction logs service
            direct_payload = {
                "payment_id": payment_record.id,
                "wallet_id": payment_record.wallet_id,
                "amount": payment_record.amount,
                "currency": payment_record.currency,
                "status": payment_record.status,
                "log_metadata": json.dumps(payment_record.payment_metadata),
                "created_at": payment_record.created_at.isoformat(),
                "completed_at": payment_record.webhook_received_at.isoformat() if payment_record.webhook_received_at else payment_record.updated_at.isoformat()
            }
            
            direct_response = requests.post(
                DIRECT_TRANSACTION_LOG_ENDPOINT,
                json=direct_payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if direct_response.status_code == 200 or direct_response.status_code == 201:
                logger.info(f"Successfully sent transaction log directly for payment {payment_record.id}")
                return True
            else:
                logger.error(f"Direct transaction log failed: {direct_response.status_code} - {direct_response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Direct transaction log request failed: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Error sending transaction log: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def update_wallet_balance(payment_record, amount_in_cents):
    """
    Update the wallet balance through the API Gateway after a successful payment.
    """
    logger.info(f"==== WALLET UPDATE ATTEMPT ====")
    logger.info(f"Payment ID: {payment_record.id}")
    logger.info(f"Payment Amount: {amount_in_cents} cents (${amount_in_cents/100})")
    logger.info(f"Payment Metadata: {payment_record.payment_metadata}")
    
    try:
        wallet_id = payment_record.payment_metadata.get('wallet_id', 23)  # Default if not found
        email = payment_record.payment_metadata.get('email')
        wallet_password = payment_record.payment_metadata.get('wallet_password', "hello")  # Get password from metadata with fallback
        
        if email is None:
            email = "default@example.com"
            logger.info("No email provided, using default email: default@example.com")
        else:
            logger.info(f"Using email: {email}")
        
        logger.info(f"Using wallet_id: {wallet_id} and email: {email}")
        
        amount_in_wallet_format = amount_in_cents / 10000
        logger.info(f"Converted amount: {amount_in_cents} cents -> {amount_in_wallet_format} wallet format")
        
        wallet_update_payload = {
            "WalletId": int(wallet_id) if isinstance(wallet_id, str) and wallet_id.isdigit() else wallet_id,
            "Password": wallet_password,  # Use password from metadata
            "ChangeAmount": amount_in_wallet_format,
            "Email": email
        }
        
        logger.info(f"Sending wallet update with payload: {wallet_update_payload}")
        
        try:
            gateway_url = "http://kong:8000"  # Hardcoded for testing
            api_url = f"{gateway_url}/api/wallet/UpdateBalance"
            logger.info(f"Calling API at: {api_url}")
            
            response = requests.put(
                api_url,
                json=wallet_update_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                try:
                    resp_data = response.json()
                    logger.info(f"Success response JSON: {resp_data}")
                except:
                    logger.info(f"Success response not JSON: {response.text}")
                return True
            else:
                logger.error(f"Error response ({response.status_code}): {response.text}")
                
                try:
                    direct_url = "https://personal-rrfqkpux.outsystemscloud.com/Wallet/rest/Wallet/UpdateBalance"
                    logger.info(f"Trying direct API call to {direct_url}")
                    direct_response = requests.put(
                        direct_url,
                        json=wallet_update_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    logger.info(f"Direct API response: {direct_response.status_code} - {direct_response.text}")
                    if direct_response.status_code == 200:
                        return True
                except Exception as e:
                    logger.error(f"Direct API call failed: {str(e)}")
                
                return False
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Connection error - could not connect to API")
            return False
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating wallet balance: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Create FastAPI app
app = FastAPI(title="Payment Microservice")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add route to serve the HTML test page
@app.get("/", response_class=HTMLResponse)
async def get_payment_page():
    try:
        with open("test.html", "r") as f:
            html_content = f.read()
        return html_content
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Payment test page not found</h1>", status_code=404)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout(payload: PaymentIntentRequest, request: Request):
    """
    Create a Stripe Checkout session for simple payment processing.
    """
    try:
        success_url = f"http://localhost:8080/frontend/index.html?success=true"
        cancel_url = f"http://localhost:8080/frontend/index.html?canceled=true"

        logger.info(f"Payload received for Stripe session: {payload.dict()}")
        
        # Create a copy of metadata to avoid modifying the original
        metadata = dict(payload.metadata) if payload.metadata else {}
        
        # Add wallet_password to metadata if provided
        if payload.wallet_password:
            metadata["wallet_password"] = payload.wallet_password
            logger.info("Added wallet_password to metadata")
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": payload.currency,
                        "product_data": {
                            "name": "Wallet Top-up",
                            "description": "Add funds to your e-wallet"
                        },
                        "unit_amount": payload.amount,
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            client_reference_id=payload.wallet_id,
            customer_email=metadata.get("email") if metadata and "email" in metadata else None,
            customer_creation="always"
        )
        
        payment_id = str(uuid.uuid4())
        
        # Store payment record in memory
        payment_record = PaymentRecord(
            id=payment_id,
            stripe_payment_id=checkout_session.id,
            amount=payload.amount,
            currency=payload.currency,
            status="pending",
            wallet_id=payload.wallet_id,
            payment_metadata=metadata
        )
        payment_records[payment_id] = payment_record
        
        # Also keep a reference by stripe session ID
        payment_records[checkout_session.id] = payment_record
        
        logger.info(f"Created checkout session: {checkout_session.id} with internal ID: {payment_id}")
        
        # Log the initial transaction
        logger.info(f"Logging initial transaction for payment {payment_id}")
        send_transaction_log(payment_record)
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "payment_id": payment_id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/success")
async def success(session_id: str):
    """
    Handle successful checkout redirect.
    """
    try:
        payment_record = payment_records.get(session_id)

        if payment_record and payment_record.status == "completed":
            logger.info(f"Payment {payment_record.id} already completed")
            return {"status": "success", "payment_id": payment_record.id, "already_processed": True}

        logger.info(f"Processing success API call for session ID: {session_id}")
        session = stripe.checkout.Session.retrieve(session_id)
        logger.info(f"Retrieved Stripe session: {session.id}, payment_status: {session.payment_status}")
        logger.info(f"Retrieved Stripe session details: {session}")

        if payment_record:
            logger.info(f"Found payment record {payment_record.id} for session {session_id}")

            if payment_record.status != "completed":
                payment_record.update_status("completed" if session.payment_status == "paid" else session.payment_status)

                if session.customer_details and session.customer_details.email:
                    payment_record.payment_metadata['email'] = session.customer_details.email
                    logger.info(f"Added customer email to payment metadata: {session.customer_details.email}")
                
                logger.info(f"Payment metadata after update: {payment_record.payment_metadata}")
                logger.info(f"Updated payment record status to: {payment_record.status}")

                if session.payment_status == "paid":
                    amount = payment_record.amount  # Amount in cents
                    logger.info(f"Success handler: Updating wallet for payment {payment_record.id}, amount: {amount}")
                    wallet_updated = await update_wallet_balance(payment_record, amount)

                    if wallet_updated:
                        logger.info(f"Success handler: Wallet balance updated for payment {payment_record.id}")
                    else:
                        logger.warning(f"Success handler: Failed to update wallet balance for payment {payment_record.id}")

                notify_payment_status(payment_record)
                send_transaction_log(payment_record)
            else:
                logger.info(f"Payment record {payment_record.id} already completed, no update needed")
        else:
            logger.warning(f"No payment record found for session {session_id}")
            # Create a new record if we don't have one (e.g., if the server restarted)
            session = stripe.checkout.Session.retrieve(session_id)
            if session and session.payment_status == "paid":
                payment_id = str(uuid.uuid4())
                payment_record = PaymentRecord(
                    id=payment_id,
                    stripe_payment_id=session_id,
                    amount=session.amount_total,
                    currency=session.currency,
                    status="completed",
                    wallet_id=session.client_reference_id,
                    payment_metadata=session.metadata
                )
                payment_records[payment_id] = payment_record
                payment_records[session_id] = payment_record
                
                if session.customer_details and session.customer_details.email:
                    payment_record.payment_metadata['email'] = session.customer_details.email
                
                logger.info(f"Created new payment record for session {session_id}")
                
                amount = payment_record.amount
                await update_wallet_balance(payment_record, amount)
                notify_payment_status(payment_record)
                send_transaction_log(payment_record)

        return {"status": "success", "payment_id": payment_record.id if payment_record else None}

    except Exception as e:
        logger.error(f"Error processing success callback: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error processing success callback")

@app.get("/cancel")
async def cancel():
    """
    Handle cancelled checkout.
    """
    return {"status": "cancelled"}

@app.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
            logger.warning("Webhook signature not verified (no secret provided)")
            
        logger.info(f"Webhook received: {event.type}")
        
        if event.type == "checkout.session.completed":
            session = event.data.object
            payment_record = payment_records.get(session.id)
            
            if payment_record:
                payment_record.update_status("completed")
                payment_record.mark_webhook_received()
                
                if session.customer_details and session.customer_details.email:
                    payment_record.payment_metadata['email'] = session.customer_details.email
                    logger.info(f"Added customer email to payment metadata: {session.customer_details.email}")
                
                amount = payment_record.amount  # Amount in cents
                wallet_updated = await update_wallet_balance(payment_record, amount)
                
                if wallet_updated:
                    logger.info(f"Wallet balance updated for payment {payment_record.id}")
                else:
                    logger.warning(f"Failed to update wallet balance for payment {payment_record.id}")
                
                notify_payment_status(payment_record)
                send_transaction_log(payment_record)
                
                logger.info(f"Payment {payment_record.id} marked as completed via webhook")
            else:
                # Create a new record if we don't have one (e.g., if the server restarted)
                payment_id = str(uuid.uuid4())
                metadata = session.metadata.to_dict() if hasattr(session.metadata, 'to_dict') else session.metadata or {}
                
                payment_record = PaymentRecord(
                    id=payment_id,
                    stripe_payment_id=session.id,
                    amount=session.amount_total,
                    currency=session.currency,
                    status="completed",
                    wallet_id=session.client_reference_id,
                    payment_metadata=metadata
                )
                payment_record.mark_webhook_received()
                
                if session.customer_details and session.customer_details.email:
                    payment_record.payment_metadata['email'] = session.customer_details.email
                
                payment_records[payment_id] = payment_record
                payment_records[session.id] = payment_record
                
                amount = payment_record.amount
                await update_wallet_balance(payment_record, amount)
                notify_payment_status(payment_record)
                send_transaction_log(payment_record)
                
                logger.info(f"Created new payment record for webhook event {session.id}")
        
        elif event.type == "checkout.session.async_payment_succeeded":
            session = event.data.object
            payment_record = payment_records.get(session.id)
            
            if payment_record:
                payment_record.update_status("completed")
                payment_record.mark_webhook_received()
                
                if session.customer_details and session.customer_details.email:
                    payment_record.payment_metadata['email'] = session.customer_details.email
                
                amount = payment_record.amount
                await update_wallet_balance(payment_record, amount)
                notify_payment_status(payment_record)
                send_transaction_log(payment_record)
            else:
                # Create new record similar to above
                logger.info(f"No record found for async payment success webhook, creating new one")
                # Implementation similar to above
        
        elif event.type == "checkout.session.async_payment_failed":
            session = event.data.object
            payment_record = payment_records.get(session.id)
            
            if payment_record:
                payment_record.update_status("failed")
                payment_record.mark_webhook_received()
                notify_payment_status(payment_record)
                send_transaction_log(payment_record)
        
        return {"status": "success"}
        
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing webhook")

@app.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    """
    Retrieve payment details by ID.
    """
    payment_record = payment_records.get(payment_id)
    
    if not payment_record:
        # Check if this is a Stripe session ID
        if payment_id.startswith("cs_"):
            payment_record = payment_records.get(payment_id)
    
    if not payment_record:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment_record.to_dict()

@app.get("/payments/user/{wallet_id}")
async def list_user_payments(wallet_id: str):
    """
    Return payment history filtered by wallet_id.
    """
    user_payments = []
    for payment in payment_records.values():
        if isinstance(payment, PaymentRecord) and payment.wallet_id == wallet_id:
            user_payments.append({
                "id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "created_at": payment.created_at.isoformat(),
            })
    
    # Sort by created_at (most recent first)
    user_payments.sort(key=lambda x: x["created_at"], reverse=True)
    return user_payments

@app.get("/payments")
async def list_payments():
    """List all payments"""
    result = []
    # Filter out duplicate references (we have both payment_id and stripe_id as keys)
    unique_payments = {}
    for payment in payment_records.values():
        if isinstance(payment, PaymentRecord) and payment.id not in unique_payments:
            unique_payments[payment.id] = payment.to_dict()
    
    return list(unique_payments.values())

@app.post("/webhook-debug")
async def webhook_debug(request: Request):
    """
    Debug endpoint that logs webhook data without processing it.
    """
    body = await request.body()
    headers = dict(request.headers)
    logger.info(f"Webhook debug - Headers: {headers}, Body: {body.decode()}")
    return {"status": "logged"}

# Start the app if run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)