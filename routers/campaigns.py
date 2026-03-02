"""
AdBoost - Campaigns Router
CRUD operations for marketing campaigns
"""

from fastapi import APIRouter, HTTPException
from data_models.schemas import CampaignCreate, CampaignResponse
from data_models.database import create_campaign, get_campaign, list_campaigns

router = APIRouter()


@router.post("/", response_model=CampaignResponse, summary="Create a new campaign")
async def create_new_campaign(payload: CampaignCreate):
    """
    Create a new AdBoost campaign with:
    - Campaign goal (clicks, signups, sales)
    - Target audience segment
    - Base creative (headline, body, CTA, image description)
    """
    campaign = create_campaign(payload.model_dump())
    return campaign


@router.get("/", summary="List all campaigns")
async def get_all_campaigns():
    """Retrieve all campaigns in the system."""
    return {"campaigns": list_campaigns(), "total": len(list_campaigns())}


@router.get("/{campaign_id}", response_model=CampaignResponse, summary="Get campaign by ID")
async def get_campaign_by_id(campaign_id: str):
    """Retrieve a specific campaign by ID."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")
    return campaign


@router.get("/{campaign_id}/overview", summary="Full campaign overview")
async def get_campaign_overview(campaign_id: str):
    """
    Get a complete campaign overview including:
    - Campaign details
    - All variants
    - All experiments
    - Performance summary
    """
    from data_models.database import list_variants_for_campaign, list_experiments_for_campaign

    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

    variants = list_variants_for_campaign(campaign_id)
    experiments = list_experiments_for_campaign(campaign_id)

    # Compute summary
    total_impressions = sum(v.get("impressions", 0) for v in variants)
    total_clicks = sum(v.get("clicks", 0) for v in variants)
    total_conversions = sum(v.get("conversions", 0) for v in variants)
    winners = [v for v in variants if v.get("status") == "winner"]

    return {
        "campaign": campaign,
        "stats": {
            "total_variants": len(variants),
            "total_experiments": len(experiments),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "overall_ctr": round(total_clicks / total_impressions, 4) if total_impressions > 0 else 0,
            "winners_found": len(winners),
        },
        "variants": variants,
        "experiments": experiments,
    }
