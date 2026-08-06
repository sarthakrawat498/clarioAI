from fastapi import APIRouter
from app.schemas.recommendation import PremiumEstimateRequest, PremiumEstimateResponse
from app.services.premium_service import calculate_actuarial_premium

router = APIRouter(prefix="/premium", tags=["Premium Calculator & Quotes"])


@router.post("/estimate", response_model=PremiumEstimateResponse)
def estimate_premium(req: PremiumEstimateRequest):
    """Calculate actuarial premium quote with age loading, family floater setup, and optional add-ons."""
    return calculate_actuarial_premium(req)
