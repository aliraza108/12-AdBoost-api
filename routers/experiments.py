"""
AdBoost - Experiments Router
A/B test setup, traffic simulation, and statistical analysis
"""

from fastapi import APIRouter, HTTPException
from data_models.schemas import ExperimentCreate, ExperimentSimulateRequest
from data_models.database import (
    get_campaign, get_variant, create_experiment,
    get_experiment, list_experiments_for_campaign,
    get_experiment_events,
)
from ai_agents.adboost_agents import run_experiment_agent

router = APIRouter()


@router.post("/", summary="🧪 Create a new A/B experiment")
async def create_ab_experiment(payload: ExperimentCreate):
    """
    Set up a controlled A/B experiment with:
    - Multiple variant arms
    - Traffic splitting configuration
    - Statistical confidence requirements
    - Test duration controls
    """
    campaign = get_campaign(payload.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Validate variants
    for vid in payload.variant_ids:
        if not get_variant(vid):
            raise HTTPException(status_code=404, detail=f"Variant '{vid}' not found")

    # Auto-generate equal traffic split if not provided
    traffic_split = payload.traffic_split
    if not traffic_split:
        equal_share = round(100 / len(payload.variant_ids), 2)
        traffic_split = {vid: equal_share for vid in payload.variant_ids}

    experiment_data = {
        "campaign_id": payload.campaign_id,
        "variant_ids": payload.variant_ids,
        "traffic_split": traffic_split,
        "target_sample_size": payload.target_sample_size,
        "confidence_level": payload.confidence_level,
        "duration_hours": payload.duration_hours,
    }

    experiment = create_experiment(experiment_data)

    # Update variant statuses
    from data_models.database import _variants
    for vid in payload.variant_ids:
        if v := _variants.get(vid):
            v["status"] = "testing"

    return {
        "experiment": experiment,
        "message": f"✅ Experiment created with {len(payload.variant_ids)} variants",
        "traffic_split": traffic_split,
        "instructions": "Use POST /simulate to generate traffic data, then POST /analyze for results",
    }


@router.post("/simulate", summary="▶️ Simulate experiment traffic")
async def simulate_traffic(payload: ExperimentSimulateRequest):
    """
    Simulate real user traffic through the experiment.
    Uses predicted CTR/CVR to generate realistic impression/click/conversion data.

    In production, this would be replaced by real traffic routing.
    """
    experiment = get_experiment(payload.experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment["status"] == "completed":
        raise HTTPException(status_code=400, detail="Experiment already completed. Create a new one.")

    prompt = f"""
    Simulate and analyze traffic for experiment: {payload.experiment_id}
    
    Configuration:
    - Variants: {experiment['variant_ids']}
    - Traffic split: {experiment['traffic_split']}
    - Number of events to simulate: {payload.num_events}
    - Target sample size: {experiment['target_sample_size']}
    - Required confidence: {experiment['confidence_level']}
    
    Steps:
    1. Use simulate_experiment_traffic to generate {payload.num_events} events
    2. Use calculate_statistical_significance to check if we have a winner
    3. Report current experiment status clearly
    4. If significant: announce winner and confidence level
    5. If not significant: explain how much more traffic is needed
    """

    agent_response = await run_experiment_agent(prompt)
    updated_experiment = get_experiment(payload.experiment_id)

    return {
        "experiment_id": payload.experiment_id,
        "events_simulated": payload.num_events,
        "experiment_status": updated_experiment,
        "analysis": agent_response,
    }


@router.post("/{experiment_id}/analyze", summary="📈 Run statistical analysis")
async def analyze_experiment(experiment_id: str):
    """
    Run full statistical significance analysis on current experiment data.
    Uses chi-square test to determine if variant differences are real.
    """
    experiment = get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    prompt = f"""
    Perform complete statistical analysis for experiment: {experiment_id}
    
    1. Use calculate_statistical_significance to get full results
    2. Interpret the significance value (>0.95 = statistically significant)
    3. Identify the winner clearly
    4. Explain what the data means for the campaign
    5. Provide confidence in the results
    """

    agent_response = await run_experiment_agent(prompt)
    updated_experiment = get_experiment(experiment_id)

    return {
        "experiment_id": experiment_id,
        "current_state": updated_experiment,
        "statistical_analysis": agent_response,
    }


@router.get("/{experiment_id}", summary="Get experiment details")
async def get_experiment_details(experiment_id: str):
    """Get full experiment details including current metrics."""
    experiment = get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    events = get_experiment_events(experiment_id)

    # Get variant metrics
    variant_metrics = []
    for vid in experiment.get("variant_ids", []):
        v = get_variant(vid)
        if v:
            variant_metrics.append({
                "id": vid,
                "headline": v.get("creative", {}).get("headline"),
                "status": v.get("status"),
                "impressions": v.get("impressions", 0),
                "clicks": v.get("clicks", 0),
                "conversions": v.get("conversions", 0),
                "ctr": v.get("ctr"),
                "cvr": v.get("cvr"),
            })

    return {
        "experiment": experiment,
        "variant_metrics": variant_metrics,
        "event_log_count": len(events),
        "recent_events": events[-10:],
    }


@router.get("/campaign/{campaign_id}", summary="List experiments for campaign")
async def list_campaign_experiments(campaign_id: str):
    """List all experiments for a campaign."""
    experiments = list_experiments_for_campaign(campaign_id)
    return {
        "campaign_id": campaign_id,
        "total": len(experiments),
        "experiments": experiments,
    }
