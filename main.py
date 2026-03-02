"""
AdBoost - AI Marketing Creative A/B Optimization Engine
Main FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import campaigns, variants, experiments, analytics, optimize
from data_models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup"""
    await init_db()
    print("✅ AdBoost Engine initialized")
    yield
    print("🔴 AdBoost Engine shutting down")


app = FastAPI(
    title="AdBoost - AI Marketing Creative A/B Optimization Engine",
    description="""
    🚀 **AdBoost** is an autonomous AI marketing experimentation engine that:
    - Generates creative ad variants using AI
    - Predicts performance before publishing
    - Runs A/B experiments with statistical significance
    - Analyzes results and identifies winning patterns
    - Continuously optimizes campaigns in a closed loop

    Powered by OpenAI Agents SDK for intelligent orchestration.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["📢 Campaigns"])
app.include_router(variants.router, prefix="/api/v1/variants", tags=["🎨 Variants"])
app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["🧪 Experiments"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["📊 Analytics"])
app.include_router(optimize.router, prefix="/api/v1/optimize", tags=["⚡ Optimize"])


@app.get("/", tags=["🏠 Root"])
async def root():
    return {
        "system": "AdBoost - AI Marketing Creative A/B Optimization Engine",
        "version": "1.0.0",
        "status": "🟢 operational",
        "endpoints": {
            "campaigns": "/api/v1/campaigns",
            "variants": "/api/v1/variants",
            "experiments": "/api/v1/experiments",
            "analytics": "/api/v1/analytics",
            "optimize": "/api/v1/optimize",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["🏠 Root"])
async def health_check():
    return {"status": "healthy", "engine": "AdBoost v1.0.0"}
