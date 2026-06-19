from fastapi import APIRouter, status

from app import schemas
from app.deps import CurrentUser, DbSession
from app.services import payment_service

router = APIRouter()


@router.post("", response_model=schemas.PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(body: schemas.PaymentIn, user: CurrentUser, db: DbSession):
    payment = payment_service.pay_order(db, user.id, body.order_id, body.card_token)
    return schemas.PaymentOut(payment_id=payment.id, order_id=payment.order_id, status=payment.status)
