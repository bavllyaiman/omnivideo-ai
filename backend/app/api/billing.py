from fastapi import APIRouter

router = APIRouter(tags=["Billing"])


@router.get("/plans")
async def get_plans():
    return {
        "plans": [
            {"id": "free", "name": "Free", "price": 0, "credits": 100, "storage": "10GB", "features": ["5 videos", "Basic AI analysis", "720p export"]},
            {"id": "starter", "name": "Starter", "price": 19, "credits": 500, "storage": "50GB", "features": ["50 videos", "Full AI analysis", "1080p export", "Custom thumbnails"]},
            {"id": "pro", "name": "Pro", "price": 49, "credits": 2000, "storage": "200GB", "features": ["Unlimited videos", "All AI agents", "4K export", "API access"]},
            {"id": "enterprise", "name": "Enterprise", "price": 199, "credits": 10000, "storage": "1TB", "features": ["Everything in Pro", "Custom AI models", "SLA guarantee"]},
        ]
    }


@router.get("/usage")
async def get_usage(user=None):
    return {"message": "Connect Stripe for billing"}
