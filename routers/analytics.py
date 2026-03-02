"""
AdBoost - Analytics Router
Winning pattern detection, insight extraction, and performance reporting
"""

from fastapi import APIRouter, HTTPException
from data_models.database import get_campaign, get_experiment, list_experiments_for_campaign, list_variants_for_campaign
from ai_agents.adboost_agents import run_analytics_agent

router = APIRouter()


@router.get("/campaign/{campaign_id}/report", summary="📊 Full campaign analytics report")
async def get_campaign_report(campaign_id: str):
    """
    Generate a comprehensive analytics report for a campaign including:
    - Performance across all variants
    - Winning patterns identified
    - Recommendations for improvement
    - Element-level attribution
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    experiments = list_experiments_for_campaign(campaign_id)
    variants = list_variants_for_campaign(campaign_id)

    completed_experiments = [e for e in experiments if e.get("status") == "completed"]
    winners = [v for v in variants if v.get("status") == "winner"]

    if not completed_experiments:
        return {
            "campaign_id": campaign_id,
            "message": "No completed experiments yet. Run an experiment first.",
            "tip": "Use /experiments to create and simulate an A/B test",
        }

    # Build analysis prompt using most recent completed experiment
    latest_exp = sorted(completed_experiments, key=lambda x: x["created_at"], reverse=True)[0]

    best_ctr = max((v.get("ctr") or 0 for v in variants), default=0)

    prompt = f"""
    Generate a comprehensive analytics report for campaign: {campaign_id}
    Campaign goal: {campaign['goal']}
    
    Completed experiments: {len(completed_experiments)}
    Winner experiment ID: {latest_exp['id']}
    Winners found: {len(winners)}
    
    Steps:
    1. Use extract_winning_patterns for experiment: {latest_exp['id']}
    2. Use generate_improvement_recommendations for campaign: {campaign_id}
       with best current CTR: {best_ctr}
    3. Synthesize findings into:
       - What worked (element-level: headline, CTA, tone)
       - Why it worked (audience psychology)
       - What to test next (specific hypotheses)
       - Expected improvement range
    
    Make it actionable and specific for a marketing team.
    """

    agent_response = await run_analytics_agent(prompt)

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign["name"],
        "total_experiments": len(experiments),
        "completed_experiments": len(completed_experiments),
        "winners_identified": len(winners),
        "total_variants_tested": len(variants),
        "performance_summary": {
            "best_ctr": best_ctr,
            "total_impressions": sum(v.get("impressions", 0) for v in variants),
            "total_clicks": sum(v.get("clicks", 0) for v in variants),
        },
        "ai_report": agent_response,
        "winners": winners,
    }


@router.get("/experiment/{experiment_id}/insights", summary="🔍 Extract experiment insights")
async def get_experiment_insights(experiment_id: str):
    """
    Deep-dive analysis of a specific experiment.
    Extracts winning patterns and generates actionable recommendations.
    """
    experiment = get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if not experiment.get("winner_id"):
        raise HTTPException(
            status_code=400,
            detail="No winner yet. Simulate traffic and run statistical analysis first.",
        )

    campaign = get_campaign(experiment["campaign_id"])
    best_ctr = 0.05  # Default fallback

    prompt = f"""
    Extract deep insights from experiment: {experiment_id}
    
    This experiment ran for campaign: {experiment['campaign_id']}
    Current winner: {experiment.get('winner_id')}
    Statistical significance: {experiment.get('statistical_significance')}
    
    1. Use extract_winning_patterns to understand what drove the win
    2. Use generate_improvement_recommendations for next iteration
       (campaign_id: {experiment['campaign_id']}, current_best_ctr: {best_ctr})
    3. Provide:
       - 3 key lessons from this experiment
       - The core psychological mechanism at play
       - 3 specific headlines to test next
       - 2 CTA variations to try
    """

    agent_response = await run_analytics_agent(prompt)

    return {
        "experiment_id": experiment_id,
        "winner_id": experiment.get("winner_id"),
        "confidence": experiment.get("statistical_significance"),
        "insights": agent_response,
    }


@router.get("/campaign/{campaign_id}/trends", summary="📈 Performance trends")
async def get_performance_trends(campaign_id: str):
    """
    Analyze performance trends across all variants for a campaign.
    Shows which elements consistently outperform.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    variants = list_variants_for_campaign(campaign_id)

    if not variants:
        return {"message": "No variants yet. Generate variants first."}

    # Group by tone
    tone_performance: dict = {}
    for v in variants:
        tone = v.get("creative", {}).get("tone", "unknown")
        ctr = v.get("ctr") or 0
        if tone not in tone_performance:
            tone_performance[tone] = []
        tone_performance[tone].append(ctr)

    tone_avg = {
        tone: round(sum(ctrs) / len(ctrs), 4)
        for tone, ctrs in tone_performance.items()
        if ctrs
    }

    # Sort variants by CTR
    sorted_variants = sorted(variants, key=lambda x: x.get("ctr") or 0, reverse=True)

    return {
        "campaign_id": campaign_id,
        "total_variants": len(variants),
        "tone_performance_avg": tone_avg,
        "top_performer": sorted_variants[0] if sorted_variants else None,
        "bottom_performer": sorted_variants[-1] if len(sorted_variants) > 1 else None,
        "all_variants_ranked": sorted_variants,
    }
