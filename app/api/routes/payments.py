from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional, Dict, Any

from app.dependencies import get_current_user
from app.models.payment import PaymentInitiateRequest, PaymentInitiateResponse, PaymentProvider
from app.services.payment_service import payment_service

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    payload: PaymentInitiateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Initiate a payment for a booking.
    """
    # 1. Validate Booking (ensure user owns it, get amount) - Mocked for scaffold
    amount = 50.00 # Placeholder: fetch from booking
    
    try:
        response = await payment_service.initiate_payment(
            booking_id=payload.bookingId,
            amount=amount,
            provider=payload.provider,
            currency=payload.currency,
            return_url=payload.returnUrl
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Payment initiation failed")

@router.post("/webhook/{provider}")
async def payment_webhook(
    provider: PaymentProvider,
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    x_signature: Optional[str] = Header(None, alias="X-Signature"), # For generic/MTN
):
    """
    Webhook endpoint for payment providers.
    """
    try:
        payload = await request.json()
        signature = stripe_signature if provider == PaymentProvider.STRIPE else x_signature
        
        await payment_service.process_webhook(provider, payload, signature or "")
        return {"received": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
