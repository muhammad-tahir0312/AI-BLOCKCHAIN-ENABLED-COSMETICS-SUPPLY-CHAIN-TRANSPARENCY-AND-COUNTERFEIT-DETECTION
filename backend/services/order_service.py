from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import models
from loguru import logger

class OrderService:
    @staticmethod
    async def create_order(db: Session, order_data: dict, consumer_id: int):
        try:
            # Verify product exists
            product = db.query(models.Product).filter(
                models.Product.id == order_data["product_id"]
            ).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            new_order = models.Order(
                **order_data,
                consumer_id=consumer_id,
                status="NEW"
            )
            
            db.add(new_order)
            db.commit()
            db.refresh(new_order)
            return new_order
            
        except Exception as e:
            db.rollback()
            logger.error(f"Order creation failed: {str(e)}")
            raise

    @staticmethod
    async def update_order_status(
        db: Session, 
        order_id: int, 
        status_data: dict
    ):
        try:
            order = db.query(models.Order).filter(
                models.Order.id == order_id
            ).first()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )

            for key, value in status_data.items():
                setattr(order, key, value)
            
            db.commit()
            db.refresh(order)
            return order
            
        except Exception as e:
            db.rollback()
            logger.error(f"Order update failed: {str(e)}")
            raise

    @staticmethod
    def get_order(db: Session, order_id: int):
        order = db.query(models.Order).filter(
            models.Order.id == order_id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        return order

    @staticmethod
    def get_all_orders(db: Session, consumer_id: int = None):
        query = db.query(models.Order)
        if consumer_id:
            query = query.filter(models.Order.consumer_id == consumer_id)
        return query.all()

    @staticmethod
    def get_delivered_orders(db: Session):
        return db.query(models.Order).filter(
            models.Order.status == "DELIVERED"
        ).all()