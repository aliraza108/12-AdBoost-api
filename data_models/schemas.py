"""
AdBoost - Pydantic Schemas
Request/Response models for all API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class CampaignGoal(str, Enum):
    clicks = "clicks"
    signups = "signups"
    sales = "sales"
    impressions = "impressions"
    leads = "leads"


class VariantStatus(str, Enum):
    draft = "draft"
    testing = "testing"
    winner = "winner"
    loser = "loser"
    paused = "paused"


class ExperimentStatus(str, Enum):
    running = "running"
    completed = "completed"
    paused = "paused"
    insufficient_data = "insufficient_data"


class ToneStyle(str, Enum):
    urgency = "urgency"
    curiosity = "curiosity"
    social_proof = "social_proof"
    benefit_driven = "benefit_driven"
    fear_of_missing_out = "fear_of_missing_out"
    empathy = "empathy"
    authority = "authority"
    humor = "humor"


# ─── Creative Schemas ─────────────────────────────────────────────────────────

class BaseCreative(BaseModel):
    headline: str = Field(..., description="Main headline text")
    body: Optional[str] = Field(None, description="Body copy")
    cta: str = Field(..., description="Call-to-action button text")
    image_description: Optional[str] = Field(None, description="Image description for visual")


class VariantCreative(BaseCreative):
    tone: Optional[ToneStyle] = None
    emotional_trigger: Optional[str] = None
    predicted_ctr: Optional[float] = None
    predicted_cvr: Optional[float] = None
    engagement_score: Optional[float] = None
    ai_reasoning: Optional[str] = None


# ─── Campaign Schemas ─────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str = Field(..., description="Campaign name")
    goal: CampaignGoal = Field(..., description="Primary optimization goal")
    audience_segment: str = Field(..., description="Target audience description")
    base_creative: BaseCreative
    budget: Optional[float] = Field(None, description="Campaign budget in USD")
    tags: Optional[List[str]] = Field(default=[], description="Campaign tags")


class CampaignResponse(BaseModel):
    id: str
    name: str
    goal: str
    audience_segment: str
    base_creative: dict
    status: str
    created_at: str
    budget: Optional[float] = None
    tags: List[str] = []


# ─── Variant Schemas ──────────────────────────────────────────────────────────

class VariantGenerateRequest(BaseModel):
    campaign_id: str = Field(..., description="Campaign ID to generate variants for")
    num_variants: int = Field(default=3, ge=2, le=8, description="Number of variants to generate")
    tones: Optional[List[ToneStyle]] = Field(default=None, description="Specific tones to target")
    focus_element: Optional[Literal["headline", "cta", "body", "all"]] = Field(
        default="all", description="Which creative element to focus on"
    )


class VariantResponse(BaseModel):
    id: str
    campaign_id: str
    creative: dict
    status: str
    impressions: int
    clicks: int
    conversions: int
    ctr: Optional[float] = None
    cvr: Optional[float] = None
    created_at: str


# ─── Experiment Schemas ───────────────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    campaign_id: str
    variant_ids: List[str] = Field(..., min_length=2, description="Variant IDs to test (min 2)")
    traffic_split: Optional[Dict[str, float]] = Field(
        default=None, description="Traffic % per variant e.g. {'v1': 50, 'v2': 50}"
    )
    target_sample_size: int = Field(default=1000, description="Samples per variant for significance")
    confidence_level: float = Field(default=0.95, ge=0.80, le=0.99)
    duration_hours: Optional[int] = Field(default=72, description="Max test duration in hours")


class ExperimentSimulateRequest(BaseModel):
    experiment_id: str
    num_events: int = Field(default=500, ge=50, le=5000, description="Events to simulate")


class ExperimentResponse(BaseModel):
    id: str
    campaign_id: str
    variant_ids: List[str]
    status: str
    winner_id: Optional[str] = None
    statistical_significance: Optional[float] = None
    created_at: str
    traffic_split: Optional[dict] = None
    confidence_level: float


# ─── Analytics Schemas ────────────────────────────────────────────────────────

class AnalyticsReport(BaseModel):
    campaign_id: str
    experiment_id: Optional[str] = None
    summary: str
    winner: Optional[dict] = None
    variant_performance: List[dict]
    winning_patterns: List[str]
    recommendations: List[str]
    statistical_details: dict


# ─── Optimization Schemas ─────────────────────────────────────────────────────

class OptimizationRequest(BaseModel):
    campaign_id: str
    iterations: int = Field(default=1, ge=1, le=5, description="Number of optimization loops")


class OptimizationResult(BaseModel):
    campaign_id: str
    iteration: int
    previous_best: Optional[dict]
    new_variants: List[dict]
    predicted_improvement: str
    optimization_strategy: str
    next_steps: List[str]
