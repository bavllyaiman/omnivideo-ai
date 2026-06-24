from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.models import User
import stripe

router = APIRouter(prefix="/billing", tags=["Billing"])

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


@router.get("/plans")
async def get_plans():
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "credits": 100,
                "storage": "10GB",
                "features": ["5 videos", "Basic AI analysis", "720p export", "Email support"],
            },
            {
                "id": "starter",
                "name": "Starter",
                "price": 19,
                "credits": 500,
                "storage": "50GB",
                "features": ["50 videos", "Full AI analysis", "1080p export", "Priority support", "Custom thumbnails"],
                "stripe_price_id": settings.STRIPE_PRICE_MONTHLY,
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 49,
                "credits": 2000,
                "storage": "200GB",
                "features": ["Unlimited videos", "All AI agents", "4K export", "API access", "White label"],
                "stripe_price_id": settings.STRIPE_PRICE_MONTHLY,
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 199,
                "credits": 10000,
                "storage": "1TB",
                "features": ["Everything in Pro", "Custom AI models", "SLA guarantee", "Dedicated support", "On-premise option"],
            },
        ]
    }


@router.post("/checkout")
async def create_checkout_session(
    price_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            name=current_user.full_name,
            metadata={"user_id": str(current_user.id)},
        )
        current_user.stripe_customer_id = customer.id
        await db.flush()

    session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url="http://localhost:3000/billing/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:3000/billing/cancel",
        metadata={"user_id": str(current_user.id)},
    )

    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/portal")
async def create_billing_portal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    session = stripe.billing_portal.Session.create(
        customer=current_user.stripe_customer_id,
        return_url="http://localhost:3000/billing",
    )

    return {"portal_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.stripe_subscription_id = session["subscription"]
            from app.models.models import SubscriptionTier
            user.subscription_tier = SubscriptionTier.STARTER
            await db.flush()

    elif event["type"] == "invoice.paid":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            from app.models.models import Payment
            payment = Payment(
                user_id=user.id,
                stripe_payment_id=session["payment_intent"],
                amount=session["amount_paid"],
                currency=session["currency"],
                status="completed",
            )
            db.add(payment)
            await db.flush()

    return {"status": "ok"}


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
):
    return {
        "credits_remaining": current_user.credits_remaining,
        "credits_used": current_user.credits_used_this_month,
        "storage_used": current_user.storage_used_bytes,
        "storage_limit": current_user.storage_limit_bytes,
        "subscription_tier": current_user.subscription_tier,
    }
