from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    MTN_MOMO = "mtn_momo"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Transaction(BaseModel):
    id: Optional[str] = None
    bookingId: str
    amount: float
    currency: str = "USD"
    provider: PaymentProvider
    status: PaymentStatus = PaymentStatus.PENDING
    providerTransactionId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    metadata: Dict[str, Any] = {}

    model_config = ConfigDict(populate_by_name=True)

class PaymentInitiateRequest(BaseModel):
    bookingId: str
    provider: PaymentProvider
    currency: str = "USD" # Default to USD, but likely RWF for MTN
    returnUrl: Optional[str] = None # For Stripe redirect

class PaymentInitiateResponse(BaseModel):
    transactionId: str
    paymentUrl: Optional[str] = None # For Stripe Checkout or externally hosted page
    clientSecret: Optional[str] = None # For Stripe Elements
    message: Optional[str] = None # For MTN "Push sent" message
