import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, UTC

from app.config import settings
from app.models.payment import (
    PaymentProvider, 
    Transaction, 
    PaymentStatus, 
    PaymentInitiateResponse
)
from app.services import firebase_service

logger = logging.getLogger(__name__)

class PaymentStrategy(ABC):
    @abstractmethod
    async def initiate_payment(self, transaction: Transaction, return_url: Optional[str]) -> PaymentInitiateResponse:
        pass

    @abstractmethod
    async def handle_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        pass

class StripePaymentStrategy(PaymentStrategy):
    def __init__(self):
        # In a real app, initialize stripe.api_key = settings.STRIPE_SECRET_KEY
        pass

    async def initiate_payment(self, transaction: Transaction, return_url: Optional[str]) -> PaymentInitiateResponse:
        logger.info(f"Initiating Stripe payment for {transaction.amount} {transaction.currency}")
        # Mock logic
        return PaymentInitiateResponse(
            transactionId=transaction.id,
            paymentUrl=f"https://checkout.stripe.com/pay/mock_{transaction.id}",
            message="Redirect to paymentUrl"
        )

    async def handle_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        logger.info("Handling Stripe webhook")
        # Logic to verify signature and update transaction status
        return True

class MTNMoMoPaymentStrategy(PaymentStrategy):
    def __init__(self):
        # Initialize MTN headers/tokens
        pass
    
    async def initiate_payment(self, transaction: Transaction, return_url: Optional[str]) -> PaymentInitiateResponse:
        logger.info(f"Initiating MTN MoMo payment for {transaction.amount} {transaction.currency}")
        # Mock logic: trigger push notification
        return PaymentInitiateResponse(
            transactionId=transaction.id,
            message="Payment request sent to user's phone. Please approve."
        )

    async def handle_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        logger.info("Handling MTN MoMo webhook")
        return True

class PaymentService:
    def __init__(self):
        self._strategies: Dict[PaymentProvider, PaymentStrategy] = {
            PaymentProvider.STRIPE: StripePaymentStrategy(),
            PaymentProvider.MTN_MOMO: MTNMoMoPaymentStrategy(),
        }

    def _get_strategy(self, provider: PaymentProvider) -> PaymentStrategy:
        return self._strategies.get(provider)

    async def create_transaction(self, booking_id: str, amount: float, currency: str, provider: PaymentProvider) -> Transaction:
        """Creates a transaction record in Firestore"""
        transaction = Transaction(
            bookingId=booking_id,
            amount=amount,
            currency=currency,
            provider=provider,
            status=PaymentStatus.PENDING,
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC)
        )
        # In a real implementation: save to DB
        # ref = firebase_service.db.collection("transactions").document()
        # transaction.id = ref.id
        # ref.set(transaction.model_dump())
        transaction.id = "mock_txn_" + booking_id # Temporary mock ID
        return transaction

    async def initiate_payment(self, booking_id: str, amount: float, provider: PaymentProvider, currency: str = "USD", return_url: Optional[str] = None) -> PaymentInitiateResponse:
        strategy = self._get_strategy(provider)
        if not strategy:
            raise ValueError(f"Provider {provider} not supported")

        transaction = await self.create_transaction(booking_id, amount, currency, provider)
        return await strategy.initiate_payment(transaction, return_url)

    async def process_webhook(self, provider: PaymentProvider, payload: Dict[str, Any], signature: str):
        strategy = self._get_strategy(provider)
        if not strategy:
            raise ValueError(f"Provider {provider} not supported")
        return await strategy.handle_webhook(payload, signature)

payment_service = PaymentService()
