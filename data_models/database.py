"""
AdBoost - Database Models & In-Memory Store
In production, replace with PostgreSQL/MongoDB
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

# ─── In-Memory Data Store ────────────────────────────────────────────────────
_campaigns: Dict[str, dict] = {}
_variants: Dict[str, dict] = {}
_experiments: Dict[str, dict] = {}
_experiment_events: Dict[str, List[dict]] = {}  # experiment_id -> events


async def init_db():
    """Initialize database / seed demo data"""
    demo_campaign_id = "demo-campaign-001"
    _campaigns[demo_campaign_id] = {
        "id": demo_campaign_id,
        "name": "ProductivityApp Launch",
        "goal": "clicks",
        "audience_segment": "startup founders, 25-40, tech-savvy",
        "base_creative": {
            "headline": "Improve your productivity",
            "body": "Our app helps you get more done every day.",
            "cta": "Try Free",
            "image_description": "Person working at a clean desk with laptop",
        },
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "budget": 5000.0,
        "tags": ["saas", "productivity", "b2b"],
    }
    print(f"✅ Demo campaign seeded: {demo_campaign_id}")


# ─── CRUD Helpers ─────────────────────────────────────────────────────────────

def create_campaign(data: dict) -> dict:
    cid = str(uuid.uuid4())
    campaign = {"id": cid, "created_at": datetime.utcnow().isoformat(), "status": "active", **data}
    _campaigns[cid] = campaign
    return campaign


def get_campaign(campaign_id: str) -> Optional[dict]:
    return _campaigns.get(campaign_id)


def list_campaigns() -> List[dict]:
    return list(_campaigns.values())


def create_variant(data: dict) -> dict:
    vid = str(uuid.uuid4())
    variant = {
        "id": vid,
        "created_at": datetime.utcnow().isoformat(),
        "impressions": 0,
        "clicks": 0,
        "conversions": 0,
        **data,
    }
    _variants[vid] = variant
    return variant


def get_variant(variant_id: str) -> Optional[dict]:
    return _variants.get(variant_id)


def list_variants_for_campaign(campaign_id: str) -> List[dict]:
    return [v for v in _variants.values() if v.get("campaign_id") == campaign_id]


def update_variant_metrics(variant_id: str, impressions: int = 0, clicks: int = 0, conversions: int = 0):
    if v := _variants.get(variant_id):
        v["impressions"] += impressions
        v["clicks"] += clicks
        v["conversions"] += conversions
        v["ctr"] = round(v["clicks"] / v["impressions"], 4) if v["impressions"] > 0 else 0
        v["cvr"] = round(v["conversions"] / v["clicks"], 4) if v["clicks"] > 0 else 0


def create_experiment(data: dict) -> dict:
    eid = str(uuid.uuid4())
    experiment = {
        "id": eid,
        "created_at": datetime.utcnow().isoformat(),
        "status": "running",
        "winner_id": None,
        "statistical_significance": None,
        **data,
    }
    _experiments[eid] = experiment
    _experiment_events[eid] = []
    return experiment


def get_experiment(experiment_id: str) -> Optional[dict]:
    return _experiments.get(experiment_id)


def list_experiments_for_campaign(campaign_id: str) -> List[dict]:
    return [e for e in _experiments.values() if e.get("campaign_id") == campaign_id]


def update_experiment(experiment_id: str, updates: dict):
    if e := _experiments.get(experiment_id):
        e.update(updates)
        return e
    return None


def add_experiment_event(experiment_id: str, event: dict):
    if experiment_id in _experiment_events:
        _experiment_events[experiment_id].append({
            "timestamp": datetime.utcnow().isoformat(),
            **event,
        })


def get_experiment_events(experiment_id: str) -> List[dict]:
    return _experiment_events.get(experiment_id, [])