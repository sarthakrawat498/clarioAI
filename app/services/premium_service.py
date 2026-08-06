import logging
from typing import List
from app.schemas.recommendation import PremiumEstimateRequest, PremiumEstimateResponse, PremiumBreakdownItem

logger = logging.getLogger(__name__)


def calculate_actuarial_premium(req: PremiumEstimateRequest) -> PremiumEstimateResponse:
    """
    Calculates detailed actuarial premium quote with age loading, sum insured tier,
    floater multiplier, PED risk factor, optional riders, and 18% GST.
    """
    breakdown: List[PremiumBreakdownItem] = []

    # 1. Base Premium by Sum Insured Tier
    si = req.sum_insured
    if si <= 500000:
        base_rate = 8500.0
    elif si <= 1000000:
        base_rate = 12500.0
    elif si <= 2500000:
        base_rate = 18500.0
    else:
        base_rate = 28000.0 # 1 Cr+

    breakdown.append(PremiumBreakdownItem(
        name="Base Premium (Tier 1 City)",
        amount=base_rate,
        description=f"Base annual rate for ₹{si:,.0f} Sum Insured."
    ))
    accumulated_premium = base_rate

    # 2. Age Band Factor
    age = req.age
    age_multiplier = 1.0
    if age <= 35:
        age_multiplier = 1.0
    elif age <= 45:
        age_multiplier = 1.25
    elif age <= 55:
        age_multiplier = 1.60
    elif age <= 65:
        age_multiplier = 2.10
    else:
        age_multiplier = 2.80

    if age_multiplier > 1.0:
        age_loading = base_rate * (age_multiplier - 1.0)
        breakdown.append(PremiumBreakdownItem(
            name=f"Age Factor (Age {age})",
            amount=round(age_loading, 2),
            description=f"{int((age_multiplier - 1.0)*100)}% actuarial age risk adjustment."
        ))
        accumulated_premium += age_loading

    # 3. Coverage Type & Dependents Factor
    if req.coverage_type.lower() == "family floater" and req.family_members_count > 1:
        floater_multiplier = 0.45 * (req.family_members_count - 1)
        floater_cost = accumulated_premium * floater_multiplier
        breakdown.append(PremiumBreakdownItem(
            name=f"Family Floater ({req.family_members_count} Members)",
            amount=round(floater_cost, 2),
            description="Floater coverage multiplier for additional dependents."
        ))
        accumulated_premium += floater_cost

    # 4. Pre-Existing Diseases Loading
    peds = req.pre_existing_diseases or []
    if peds:
        ped_loading_pct = 0.15 * len(peds)
        ped_cost = accumulated_premium * ped_loading_pct
        breakdown.append(PremiumBreakdownItem(
            name=f"Pre-Existing Disease Loading ({len(peds)} declared)",
            amount=round(ped_cost, 2),
            description=f"{int(ped_loading_pct*100)}% medical underwriting risk loading."
        ))
        accumulated_premium += ped_cost

    # 5. Tobacco User Loading
    if req.tobacco_user:
        tob_cost = accumulated_premium * 0.15
        breakdown.append(PremiumBreakdownItem(
            name="Tobacco / Smoker Loading",
            amount=round(tob_cost, 2),
            description="15% actuarial tobacco mortality risk loading."
        ))
        accumulated_premium += tob_cost

    # 6. Add-on Riders
    riders = req.add_on_riders or []
    rider_prices = {
        "critical illness": 2500.0,
        "hospital cash": 1200.0,
        "maternity": 3500.0,
        "personal accident": 800.0
    }
    for r in riders:
        r_key = r.lower()
        price = rider_prices.get(r_key, 1500.0)
        breakdown.append(PremiumBreakdownItem(
            name=f"Rider: {r}",
            amount=price,
            description="Optional comprehensive protection rider."
        ))
        accumulated_premium += price

    # Subtotal before tax
    net_premium = round(accumulated_premium, 2)
    gst = round(net_premium * 0.18, 2)
    total_annual = round(net_premium + gst, 2)
    monthly_inst = round(total_annual / 12.0, 2)

    return PremiumEstimateResponse(
        total_annual_premium=total_annual,
        base_premium=net_premium,
        gst_18_percent=gst,
        monthly_installment=monthly_inst,
        breakdown=breakdown,
        policy_name=f"Comprehensive Health Policy ({req.coverage_type})"
    )
