import hashlib
import hmac
import razorpay
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db import get_db
from app.models import User, Payment
from app.core.deps import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/payment", tags=["Payment"])

# ✅ Initialize Razorpay client
rz_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


# ─── ENDPOINT 1: Create a Razorpay Order ────────────────────────────────────
@router.post("/create-order")
async def create_order(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Step 1 of payment flow.
    Frontend calls this → backend creates a Razorpay order → returns order_id to UI.
    UI then opens the Razorpay checkout popup using that order_id.
    """
    amount_paise = 9900  # ₹99 in paise (Razorpay works in lowest currency unit)

    try:
        print(f"Creating Razorpay order for user: {user_id}")
        order = rz_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "user_id": user_id,
                "plan": "premium"
            }
        })
        print(f"Order created successfully: {order['id']}")
    except Exception as e:
        print(f"Razorpay order creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Razorpay error: {str(e)}")

    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "razorpay_key": settings.RAZORPAY_KEY_ID
    }


# ─── ENDPOINT 2: Verify Payment & Activate Premium ──────────────────────────
@router.post("/verify")
async def verify_payment(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """
    Step 2 of payment flow.
    After frontend completes checkout, it sends back the 3 Razorpay IDs.
    We verify the HMAC signature to PROVE payment is genuine, then activate premium.
    """
    body = await request.json()

    razorpay_order_id   = body.get("razorpay_order_id")
    razorpay_payment_id = body.get("razorpay_payment_id")
    razorpay_signature  = body.get("razorpay_signature")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        raise HTTPException(status_code=400, detail="Missing payment fields")

    # ✅ HMAC Signature Verification — mathematically proves payment is genuine
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # ✅ Signature valid — find user and activate premium
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()

    # Extend if already premium and active, otherwise fresh activation
    if user.plan == "premium" and user.subscription_expires_at and user.subscription_expires_at > now:
        user.subscription_expires_at += timedelta(days=30)
    else:
        user.plan = "premium"
        user.subscription_expires_at = now + timedelta(days=30)

    # ✅ Save payment record
    payment = Payment(
        user_id=user.id,
        amount=99,
        status="success"
    )
    db.add(payment)
    await db.commit()

    return {
        "message": "Premium activated successfully",
        "plan": user.plan,
        "expires_at": user.subscription_expires_at
    }