"""
AdBoost - Variants Router
AI-powered creative variant generation and management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from data_models.schemas import VariantGenerateRequest, VariantResponse
from data_models.database import get_campaign, list_variants_for_campaign, get_variant
from ai_agents.adboost_agents import run_creative_agent, run_prediction_agent

router = APIRouter()


@router.post("/generate", summary="🎨 Generate AI creative variants")
async def generate_variants(payload: VariantGenerateRequest):
    """
    **AI-powered creative variant generation.**

    Uses the AdBoost Creative Agent to:
    1. Analyze campaign goal and audience
    2. Generate diverse headline, CTA, and copy variations
    3. Apply emotional triggers (urgency, curiosity, social proof, FOMO)
    4. Predict performance for each variant
    5. Save all variants for experimentation

    This is where the AI magic happens — genuine creative alternatives, not rephrasing.
    """
    campaign = get_campaign(payload.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign '{payload.campaign_id}' not found")

    # Build agent prompt
    tones_str = ", ".join(payload.tones) if payload.tones else "urgency, curiosity, social_proof, benefit_driven, fear_of_missing_out"
    prompt = f"""
    Generate {payload.num_variants} high-converting creative variants for campaign ID: {payload.campaign_id}
    
    Campaign details:
    - Name: {campaign['name']}
    - Goal: {campaign['goal']}
    - Audience: {campaign['audience_segment']}
    - Base headline: {campaign['base_creative']['headline']}
    - Base CTA: {campaign['base_creative']['cta']}
    
    Requirements:
    - Focus element: {payload.focus_element}
    - Tones to use: {tones_str}
    - Create {payload.num_variants} genuinely different variants
    - Each variant must target a different emotional trigger
    - Use predict_variant_performance for each before saving
    - Save each using save_generated_variant
    
    Return a clear summary of all variants created with predicted CTR ranking.
    """

    agent_response = await run_creative_agent(prompt)

    # Return variants from DB
    variants = list_variants_for_campaign(payload.campaign_id)
    return {
        "campaign_id": payload.campaign_id,
        "variants_generated": len(variants),
        "agent_summary": agent_response,
        "variants": variants,
    }


@router.post("/predict", summary="🔮 Predict variant performance")
async def predict_performance(campaign_id: str, variant_ids: list[str]):
    """
    Run AI performance prediction on specific variants.
    Returns CTR, CVR, and engagement score predictions with reasoning.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    variants_data = []
    for vid in variant_ids:
        v = get_variant(vid)
        if v:
            variants_data.append(v)

    if not variants_data:
        raise HTTPException(status_code=404, detail="No valid variants found")

    prompt = f"""
    Analyze and predict performance for these variants in campaign '{campaign_id}':
    
    Campaign goal: {campaign['goal']}
    Audience: {campaign['audience_segment']}
    
    Variants to analyze:
    {[f"ID: {v['id']} | Headline: {v['creative']['headline']} | CTA: {v['creative']['cta']} | Tone: {v['creative'].get('tone', 'unknown')}" for v in variants_data]}
    
    For each variant:
    1. Use predict_variant_performance with the tone and headline details
    2. Explain your reasoning
    3. Rank them from best to worst predicted CTR
    4. Identify which element is doing the most work
    """

    prediction_response = await run_prediction_agent(prompt)

    return {
        "campaign_id": campaign_id,
        "variants_analyzed": len(variants_data),
        "analysis": prediction_response,
        "variants": variants_data,
    }


@router.get("/campaign/{campaign_id}", summary="List all variants for a campaign")
async def list_campaign_variants(campaign_id: str):
    """List all generated variants for a campaign with their performance metrics."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    variants = list_variants_for_campaign(campaign_id)
    return {
        "campaign_id": campaign_id,
        "total": len(variants),
        "variants": sorted(variants, key=lambda x: x.get("ctr") or 0, reverse=True),
    }


@router.get("/{variant_id}", summary="Get a specific variant")
async def get_variant_by_id(variant_id: str):
    """Get detailed information about a specific variant."""
    variant = get_variant(variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return variant
