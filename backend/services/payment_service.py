from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Payment, Order, PaymentStatus, UserRole
from loguru import logger

class PaymentService:
    @staticmethod
    async def create_payment(db: Session, order_id: int, amount: float):
        payment = Payment(order_id=order_id, amount=amount)
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    async def process_signatures(db: Session, payment_id: int, user_role: UserRole, signed: bool):
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        order = db.query(Order).filter(Order.id == payment.order_id).first()
        
        # Update signature based on role
        if user_role == UserRole.CONSUMER:
            payment.user_signed = signed
        elif user_role == UserRole.SUPPLIER:
            payment.producer_signed = signed
        elif user_role == UserRole.ADMIN:
            payment.admin_signed = signed

        # Check conditions for payment release or refund
        if payment.status == PaymentStatus.PENDING:
            if (payment.user_signed and payment.producer_signed) or \
               (payment.admin_signed and payment.producer_signed) or \
               (payment.admin_signed and payment.user_signed):
                
                if payment.admin_signed and payment.user_signed:
                    payment.status = PaymentStatus.REFUNDED
                else:
                    payment.status = PaymentStatus.RELEASED

        db.commit()
        db.refresh(payment)
        return payment