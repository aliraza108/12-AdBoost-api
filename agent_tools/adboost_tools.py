"""
AdBoost - Agent Tools
All tool functions used by the AI agents
"""

import json
import random
import math
from typing import Optional
from data_models.database import (
    _campaigns, _variants, _experiments,
    create_variant, update_variant_metrics,
    update_experiment, add_experiment_event,
    list_variants_for_campaign, get_experiment_events,
)


# ─── Creative Generation Tools ────────────────────────────────────────────────

def get_campaign_info(campaign_id: str) -> str:
    """Retrieve campaign details including base creative and goals."""
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        return json.dumps({"error": f"Campaign {campaign_id} not found"})
    return json.dumps(campaign, indent=2)


def save_generated_variant(
    campaign_id: str,
    headline: str,
    cta: str,
    tone: str,
    emotional_trigger: str,
    ai_reasoning: str,
    body: Optional[str] = None,
    image_description: Optional[str] = None,
    predicted_ctr: Optional[float] = None,
    predicted_cvr: Optional[float] = None,
    engagement_score: Optional[float] = None,
) -> str:
    """Save a generated creative variant to the database."""
    variant = create_variant({
        "campaign_id": campaign_id,
        "creative": {
            "headline": headline,
            "body": body,
            "cta": cta,
            "image_description": image_description,
            "tone": tone,
            "emotional_trigger": emotional_trigger,
            "ai_reasoning": ai_reasoning,
        },
        "predictions": {
            "predicted_ctr": predicted_ctr,
            "predicted_cvr": predicted_cvr,
            "engagement_score": engagement_score,
        },
        "status": "draft",
        "ctr": None,
        "cvr": None,
    })
    return json.dumps({"success": True, "variant_id": variant["id"], "headline": headline})


# ─── Performance Prediction Tools ─────────────────────────────────────────────

def predict_variant_performance(
    headline: str,
    cta: str,
    tone: str,
    goal: str,
    audience_segment: str,
) -> str:
    """
    Predict CTR, CVR, and engagement score for a creative variant.
    Uses heuristic scoring based on creative elements.
    """
    # Simulate ML-based prediction with heuristics
    score_map = {
        "urgency": {"clicks": 0.85, "signups": 0.75, "sales": 0.80},
        "curiosity": {"clicks": 0.90, "signups": 0.70, "sales": 0.65},
        "social_proof": {"clicks": 0.75, "signups": 0.85, "sales": 0.88},
        "benefit_driven": {"clicks": 0.80, "signups": 0.82, "sales": 0.85},
        "fear_of_missing_out": {"clicks": 0.88, "signups": 0.78, "sales": 0.82},
        "empathy": {"clicks": 0.72, "signups": 0.80, "sales": 0.70},
        "authority": {"clicks": 0.78, "signups": 0.83, "sales": 0.90},
        "humor": {"clicks": 0.82, "signups": 0.65, "sales": 0.60},
    }

    base = score_map.get(tone, {}).get(goal, 0.75)
    noise = random.uniform(-0.05, 0.08)

    # Bonus for power words in headline
    power_words = ["double", "stop", "proven", "secret", "free", "instant", "guaranteed", "top", "best"]
    power_bonus = sum(0.02 for word in power_words if word.lower() in headline.lower())

    # CTA bonus
    cta_power = ["Get", "Start", "Try", "Claim", "Join", "Unlock"]
    cta_bonus = 0.03 if any(c in cta for c in cta_power) else 0

    predicted_ctr = round(min(0.99, base + noise + power_bonus + cta_bonus), 4)
    predicted_cvr = round(predicted_ctr * random.uniform(0.15, 0.35), 4)
    engagement_score = round((predicted_ctr * 0.6 + predicted_cvr * 0.4) * 100, 2)

    return json.dumps({
        "predicted_ctr": predicted_ctr,
        "predicted_cvr": predicted_cvr,
        "engagement_score": engagement_score,
        "confidence": "medium",
        "factors": {
            "tone_alignment": base,
            "power_words_detected": power_bonus > 0,
            "strong_cta": cta_bonus > 0,
        }
    })


# ─── Experiment Management Tools ──────────────────────────────────────────────

def simulate_experiment_traffic(
    experiment_id: str,
    num_events: int = 500,
) -> str:
    """
    Simulate real user traffic for an experiment.
    Assigns random impressions/clicks/conversions to variants based on predictions.
    """
    exp = _experiments.get(experiment_id)
    if not exp:
        return json.dumps({"error": "Experiment not found"})

    variant_ids = exp.get("variant_ids", [])
    traffic_split = exp.get("traffic_split", {})

    results = {}
    for vid in variant_ids:
        v = _variants.get(vid)
        if not v:
            continue

        # Use predicted CTR or default
        pred_ctr = v.get("predictions", {}).get("predicted_ctr") or random.uniform(0.03, 0.12)
        pred_cvr = v.get("predictions", {}).get("predicted_cvr") or random.uniform(0.01, 0.05)

        share = traffic_split.get(vid, 1 / len(variant_ids))
        impressions = int(num_events * share)
        clicks = int(impressions * pred_ctr * random.uniform(0.85, 1.15))
        conversions = int(clicks * pred_cvr * random.uniform(0.80, 1.20))

        update_variant_metrics(vid, impressions=impressions, clicks=clicks, conversions=conversions)
        add_experiment_event(experiment_id, {
            "type": "traffic_batch",
            "variant_id": vid,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
        })
        results[vid] = {
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": round(clicks / impressions, 4) if impressions > 0 else 0,
        }

    return json.dumps({"success": True, "experiment_id": experiment_id, "results": results})


def calculate_statistical_significance(experiment_id: str) -> str:
    """
    Run chi-square test to detect statistical significance between variants.
    Returns winner and confidence level.
    """
    exp = _experiments.get(experiment_id)
    if not exp:
        return json.dumps({"error": "Experiment not found"})

    variant_ids = exp.get("variant_ids", [])
    variant_data = []

    for vid in variant_ids:
        v = _variants.get(vid)
        if v and v["impressions"] > 0:
            variant_data.append({
                "id": vid,
                "headline": v.get("creative", {}).get("headline", "Unknown"),
                "impressions": v["impressions"],
                "clicks": v["clicks"],
                "conversions": v["conversions"],
                "ctr": v.get("ctr", 0),
                "cvr": v.get("cvr", 0),
            })

    if len(variant_data) < 2:
        return json.dumps({"significance": None, "message": "Insufficient data for analysis"})

    # Chi-square approximation
    total_impressions = sum(v["impressions"] for v in variant_data)
    total_clicks = sum(v["clicks"] for v in variant_data)
    expected_ctr = total_clicks / total_impressions if total_impressions > 0 else 0

    chi_sq = sum(
        ((v["clicks"] - v["impressions"] * expected_ctr) ** 2) / (v["impressions"] * expected_ctr + 1e-10)
        for v in variant_data
    )
    df = len(variant_data) - 1

    # Simplified p-value estimation
    significance = min(0.999, 1 - math.exp(-chi_sq / (2 * df + 1)))

    # Select winner (highest CTR with minimum impressions)
    winner = max(
        [v for v in variant_data if v["impressions"] >= 100],
        key=lambda x: x["ctr"],
        default=None,
    )

    result = {
        "significance": round(significance, 4),
        "chi_square": round(chi_sq, 4),
        "degrees_of_freedom": df,
        "winner_id": winner["id"] if winner else None,
        "winner_headline": winner["headline"] if winner else None,
        "winner_ctr": winner["ctr"] if winner else None,
        "is_significant": significance >= exp.get("confidence_level", 0.95),
        "variant_performance": variant_data,
    }

    # Update experiment record
    if result["is_significant"] and winner:
        update_experiment(experiment_id, {
            "status": "completed",
            "winner_id": winner["id"],
            "statistical_significance": significance,
        })
        if v := _variants.get(winner["id"]):
            v["status"] = "winner"

    return json.dumps(result)


# ─── Analytics & Insight Tools ────────────────────────────────────────────────

def extract_winning_patterns(experiment_id: str) -> str:
    """
    Analyze the winning variant to extract what made it work.
    Returns element-level attribution and actionable insights.
    """
    exp = _experiments.get(experiment_id)
    if not exp or not exp.get("winner_id"):
        return json.dumps({"error": "No winner determined yet. Run significance test first."})

    winner = _variants.get(exp["winner_id"])
    if not winner:
        return json.dumps({"error": "Winner variant data not found"})

    creative = winner.get("creative", {})
    headline = creative.get("headline", "")
    cta = creative.get("cta", "")
    tone = creative.get("tone", "")

    patterns = []
    # Headline analysis
    if any(w in headline.lower() for w in ["double", "triple", "2x", "3x"]):
        patterns.append("Quantified benefit (e.g. 'double', '2x') drives urgency")
    if any(w in headline.lower() for w in ["stop", "don't", "avoid"]):
        patterns.append("Negative framing / pain avoidance resonates with audience")
    if any(w in headline.lower() for w in ["founder", "expert", "pro", "top", "best"]):
        patterns.append("Authority and social proof in headline increases trust")
    if "?" in headline:
        patterns.append("Question format creates curiosity and engagement")
    if len(headline.split()) <= 6:
        patterns.append("Short, punchy headline outperforms verbose copy")
    if len(headline.split()) > 10:
        patterns.append("Descriptive headline provides enough context for decision")

    # CTA analysis
    if cta.startswith(("Get", "Start", "Try", "Join", "Claim")):
        patterns.append(f"Action-first CTA '{cta}' creates clear next step")
    if "Free" in cta:
        patterns.append("'Free' in CTA lowers conversion friction significantly")

    # Tone analysis
    if tone:
        patterns.append(f"'{tone}' tone aligned well with {exp.get('campaign_id', 'campaign')} goals")

    if not patterns:
        patterns = ["Consistent messaging matched audience intent", "Clear value proposition reduced decision friction"]

    return json.dumps({
        "winner_id": exp["winner_id"],
        "winning_headline": headline,
        "winning_cta": cta,
        "tone_used": tone,
        "winning_patterns": patterns,
        "performance": {
            "impressions": winner["impressions"],
            "clicks": winner["clicks"],
            "conversions": winner["conversions"],
            "ctr": winner.get("ctr"),
            "cvr": winner.get("cvr"),
        }
    })


def generate_improvement_recommendations(
    campaign_id: str,
    winning_patterns: str,
    current_best_ctr: float,
) -> str:
    """
    Generate concrete recommendations for the next optimization iteration.
    """
    patterns = json.loads(winning_patterns) if isinstance(winning_patterns, str) else winning_patterns
    pattern_list = patterns if isinstance(patterns, list) else patterns.get("winning_patterns", [])

    next_ideas = []

    if any("quantified" in p.lower() for p in pattern_list):
        next_ideas.append("Test more specific numbers: '7 days' → '3 days', '10x ROI'")
    if any("authority" in p.lower() for p in pattern_list):
        next_ideas.append("Add specific social proof: 'Used by 10,000 founders at Y Combinator'")
    if any("short" in p.lower() for p in pattern_list):
        next_ideas.append("A/B test ultra-short vs. medium variants (3 words vs. 8 words)")
    if any("free" in p.lower() for p in pattern_list):
        next_ideas.append("Test 'Free' alternatives: 'No credit card', 'Instant access', 'Risk-free'")

    # Always add general recommendations
    next_ideas.extend([
        "Test personalization tokens: add audience-specific language",
        "Experiment with emoji in headline for mobile audiences",
        "Try question-format headlines to increase curiosity clicks",
        f"Current best CTR {current_best_ctr:.2%} — target +15% in next iteration",
    ])

    return json.dumps({
        "campaign_id": campaign_id,
        "recommendations": next_ideas[:5],
        "optimization_hypothesis": f"Based on winning patterns, next variants should amplify {pattern_list[0] if pattern_list else 'emotional resonance'}",
        "projected_ctr_improvement": f"+{random.uniform(8, 22):.1f}%",
    })
