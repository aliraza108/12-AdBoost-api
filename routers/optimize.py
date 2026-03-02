"""
AdBoost - Optimize Router
Autonomous closed-loop optimization: generate → test → learn → improve
"""

from fastapi import APIRouter, HTTPException
from data_models.schemas import OptimizationRequest
from data_models.database import (
    get_campaign, list_variants_for_campaign,
    list_experiments_for_campaign, create_experiment,
    _variants,
)
from ai_agents.adboost_agents import run_optimization_agent, run_creative_agent, run_experiment_agent

router = APIRouter()


@router.post("/loop", summary="⚡ Run full optimization loop")
async def run_optimization_loop(payload: OptimizationRequest):
    """
    **The crown jewel of AdBoost — autonomous optimization.**

    Runs a complete closed-loop optimization cycle:
    1. **Analyze** current best performers and learn patterns
    2. **Generate** improved variants based on learnings
    3. **Plan** next experiment configuration
    4. **Report** strategy with projected improvement

    Each iteration the system gets smarter.
    Set `iterations=3` to run multiple loops in sequence.
    """
    campaign = get_campaign(payload.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    all_iteration_results = []

    for i in range(1, payload.iterations + 1):
        variants = list_variants_for_campaign(payload.campaign_id)
        experiments = list_experiments_for_campaign(payload.campaign_id)
        completed_exp = [e for e in experiments if e.get("status") == "completed"]
        winners = [v for v in variants if v.get("status") == "winner"]

        best_ctr = max((v.get("ctr") or 0 for v in variants), default=0)
        previous_winner = winners[-1] if winners else None

        prompt = f"""
        Run optimization iteration {i} of {payload.iterations} for campaign: {payload.campaign_id}
        
        Current state:
        - Campaign: {campaign['name']}
        - Goal: {campaign['goal']}
        - Audience: {campaign['audience_segment']}
        - Variants tested so far: {len(variants)}
        - Completed experiments: {len(completed_exp)}
        - Current best CTR: {best_ctr:.4f}
        - Previous winner: {previous_winner['creative']['headline'] if previous_winner else 'None yet'}
        
        Optimization tasks for this iteration:
        1. Get campaign info to understand the full context
        2. If there are completed experiments, extract winning patterns
        3. Generate improvement recommendations based on learnings
        4. Design 2-3 NEW variant hypotheses to test next
        5. Use predict_variant_performance to validate each hypothesis
        6. Save the best 2 variants using save_generated_variant
        7. Create a clear optimization strategy document
        
        Optimization philosophy:
        - Build on what worked, eliminate what didn't
        - Each iteration should target a specific conversion lever
        - Be bold: test radical alternatives alongside incremental improvements
        - Always connect recommendations to audience psychology
        
        Output format:
        - What we learned from previous iterations
        - New hypothesis being tested
        - Expected performance improvement
        - Specific elements changed and why
        """

        agent_response = await run_optimization_agent(prompt)

        new_variants = list_variants_for_campaign(payload.campaign_id)
        new_in_this_iteration = new_variants[len(variants):]

        iteration_result = {
            "iteration": i,
            "variants_before": len(variants),
            "variants_after": len(new_variants),
            "new_variants_created": len(new_in_this_iteration),
            "current_best_ctr": best_ctr,
            "strategy": agent_response,
            "new_variants": new_in_this_iteration,
        }
        all_iteration_results.append(iteration_result)

    final_variants = list_variants_for_campaign(payload.campaign_id)

    return {
        "campaign_id": payload.campaign_id,
        "optimization_complete": True,
        "total_iterations": payload.iterations,
        "total_variants_in_system": len(final_variants),
        "iterations": all_iteration_results,
        "next_step": "Run POST /experiments to launch an A/B test with the new variants",
    }


@router.post("/auto-experiment", summary="🤖 Auto-create and run experiment")
async def auto_experiment(campaign_id: str, num_variants: int = 3):
    """
    **One-click automated experiment.**

    Automatically:
    1. Takes the top N variants by predicted CTR
    2. Creates an experiment with equal traffic split
    3. Simulates initial traffic (1000 events)
    4. Returns preliminary results

    Perfect for quickly testing the latest generated variants.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get draft variants with predictions
    variants = list_variants_for_campaign(campaign_id)
    draft_variants = [v for v in variants if v.get("status") in ("draft", None)]

    if len(draft_variants) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 2 draft variants. Found {len(draft_variants)}. Generate variants first.",
        )

    # Select top variants by engagement score
    scored = sorted(
        draft_variants,
        key=lambda v: v.get("predictions", {}).get("engagement_score") or 0,
        reverse=True,
    )
    selected = scored[:num_variants]
    selected_ids = [v["id"] for v in selected]

    # Create experiment
    equal_share = round(100 / len(selected_ids), 2)
    traffic_split = {vid: equal_share for vid in selected_ids}

    experiment = create_experiment({
        "campaign_id": campaign_id,
        "variant_ids": selected_ids,
        "traffic_split": traffic_split,
        "confidence_level": 0.95,
        "target_sample_size": 1000,
    })

    # Mark variants as testing
    for vid in selected_ids:
        if v := _variants.get(vid):
            v["status"] = "testing"

    # Auto-simulate initial traffic
    prompt = f"""
    Auto-run experiment {experiment['id']} for campaign {campaign_id}.
    
    1. Simulate 1000 traffic events across variants: {selected_ids}
    2. Run statistical significance analysis
    3. Report preliminary results
    """
    agent_response = await run_experiment_agent(prompt)

    updated_experiment = list_experiments_for_campaign(campaign_id)[-1]

    return {
        "experiment": updated_experiment,
        "variants_in_test": selected,
        "auto_analysis": agent_response,
        "message": "✅ Auto-experiment running! Check /experiments/{id} for live results.",
    }


@router.get("/campaign/{campaign_id}/status", summary="🎯 Optimization status")
async def get_optimization_status(campaign_id: str):
    """
    Get a high-level optimization status summary for a campaign.
    Shows where you are in the optimization journey.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    variants = list_variants_for_campaign(campaign_id)
    experiments = list_experiments_for_campaign(campaign_id)

    total = len(variants)
    winners = [v for v in variants if v.get("status") == "winner"]
    completed_exp = [e for e in experiments if e.get("status") == "completed"]

    # Determine optimization phase
    if total == 0:
        phase = "🌱 Starting — Generate your first variants"
        progress = 0
    elif len(experiments) == 0:
        phase = "🎨 Variants ready — Create an experiment"
        progress = 25
    elif not completed_exp:
        phase = "🧪 Experiment running — Waiting for significance"
        progress = 50
    elif not winners:
        phase = "📊 Analyzing — Extracting insights"
        progress = 75
    else:
        phase = "🏆 Optimizing — Winner found, iterating"
        progress = 90

    best_variant = max(variants, key=lambda x: x.get("ctr") or 0, default=None)

    return {
        "campaign_id": campaign_id,
        "phase": phase,
        "progress_pct": progress,
        "stats": {
            "variants_generated": total,
            "experiments_run": len(experiments),
            "experiments_completed": len(completed_exp),
            "winners_found": len(winners),
        },
        "best_variant": {
            "headline": best_variant["creative"]["headline"] if best_variant else None,
            "ctr": best_variant.get("ctr") if best_variant else None,
        },
        "recommended_next_action": (
            "POST /variants/generate" if total == 0
            else "POST /experiments" if len(experiments) == 0
            else "POST /experiments/simulate" if not completed_exp
            else "POST /optimize/loop" if not winners
            else "POST /optimize/loop with iterations=2"
        ),
    }
