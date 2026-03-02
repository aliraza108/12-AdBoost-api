# ⚡ AdBoost — AI Marketing Creative A/B Optimization Engine

> Autonomous AI experimentation scientist for marketing teams.

## 🧠 What It Does

AdBoost turns any base creative into a self-improving marketing machine:

```
Input:  "Improve your productivity"
        
Output: ✅ Generates variants with different tones
        ✅ Predicts CTR before publishing
        ✅ Runs A/B experiments
        ✅ Identifies winner with statistical proof
        ✅ Explains WHY it won
        ✅ Generates improved version
        ♾️  Repeats forever
```

## 🏗️ Architecture

```
adboost/
├── main.py                         # FastAPI app + lifespan
├── requirements.txt
├── .env.example
│
├── ai_agents/                      # ✅ NOT "agents/" (conflicts with openai-agents SDK)
│   └── adboost_agents.py           # 5 specialized AI agents (OpenAI Agents SDK)
│       ├── creative_agent           → Generates ad variants
│       ├── prediction_agent         → Predicts CTR/CVR
│       ├── experiment_agent         → Manages A/B tests
│       ├── analytics_agent          → Extracts insights
│       └── optimization_agent       → Orchestrates the loop
│
├── agent_tools/                    # ✅ NOT "tools/" (can shadow stdlib)
│   └── adboost_tools.py            # Agent tool functions
│       ├── get_campaign_info()
│       ├── save_generated_variant()
│       ├── predict_variant_performance()
│       ├── simulate_experiment_traffic()
│       ├── calculate_statistical_significance()
│       ├── extract_winning_patterns()
│       └── generate_improvement_recommendations()
│
├── routers/
│   ├── campaigns.py                # Campaign CRUD
│   ├── variants.py                 # AI variant generation
│   ├── experiments.py              # A/B test management
│   ├── analytics.py                # Insights & reports
│   └── optimize.py                 # Closed-loop optimization
│
└── data_models/                    # ✅ NOT "models/" (conflicts with many ML libs)
    ├── database.py                 # In-memory data store + CRUD
    └── schemas.py                  # Pydantic request/response models
```

## 🤖 Agent System (OpenAI Agents SDK)

```python
from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from openai import AsyncOpenAI

# Configure client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)
set_default_openai_api("chat_completions")
set_default_openai_client(client=client)

# Each agent has a specific role and tools
creative_agent = Agent(
    name="AdBoost Creative Generator",
    instructions="...",
    model="gpt-4o-mini",
    tools=[get_campaign_info, predict_variant_performance, save_generated_variant],
)

# Async execution
result = await Runner.run(creative_agent, prompt)
```

### Using Gemini Instead

```python
# In agents/adboost_agents.py:
client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=GEMINI_API_KEY,
)
MODEL = "gemini-2.5-flash"
set_default_openai_client(client=client)
```

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your API key
```

### 3. Start the server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open API docs
```
http://localhost:8000/docs
```

## 🗺️ API Workflow

### Full optimization cycle (recommended order):

```bash
# Step 1: Create a campaign
POST /api/v1/campaigns/
{
  "name": "ProductivityApp Q1",
  "goal": "clicks",
  "audience_segment": "startup founders, 25-40, tech-savvy",
  "base_creative": {
    "headline": "Improve your productivity",
    "cta": "Try Free",
    "image_description": "Person at clean desk with laptop"
  }
}

# Step 2: Generate AI variants
POST /api/v1/variants/generate
{
  "campaign_id": "your-campaign-id",
  "num_variants": 4,
  "tones": ["urgency", "curiosity", "social_proof", "benefit_driven"]
}

# Step 3: Create A/B experiment
POST /api/v1/experiments/
{
  "campaign_id": "your-campaign-id",
  "variant_ids": ["variant-1", "variant-2", "variant-3"],
  "confidence_level": 0.95
}

# Step 4: Simulate traffic
POST /api/v1/experiments/simulate
{
  "experiment_id": "your-experiment-id",
  "num_events": 2000
}

# Step 5: Get insights
GET /api/v1/analytics/experiment/{experiment_id}/insights

# Step 6: Run optimization loop
POST /api/v1/optimize/loop
{
  "campaign_id": "your-campaign-id",
  "iterations": 2
}

# Or use one-click auto-experiment
POST /api/v1/optimize/auto-experiment?campaign_id=xxx&num_variants=3
```

### Use the demo campaign:
```bash
# Demo campaign pre-loaded on startup
GET /api/v1/campaigns/demo-campaign-001
```

## 📊 Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/campaigns/` | Create campaign |
| GET | `/api/v1/campaigns/{id}/overview` | Full campaign overview |
| POST | `/api/v1/variants/generate` | 🎨 AI variant generation |
| POST | `/api/v1/variants/predict` | 🔮 Performance prediction |
| POST | `/api/v1/experiments/` | Create A/B experiment |
| POST | `/api/v1/experiments/simulate` | Simulate traffic |
| POST | `/api/v1/experiments/{id}/analyze` | Statistical analysis |
| GET | `/api/v1/analytics/campaign/{id}/report` | Full AI report |
| GET | `/api/v1/analytics/experiment/{id}/insights` | Winning patterns |
| POST | `/api/v1/optimize/loop` | ⚡ Autonomous optimization |
| POST | `/api/v1/optimize/auto-experiment` | 🤖 One-click test |
| GET | `/api/v1/optimize/campaign/{id}/status` | Optimization phase |

## 🧪 Statistical Analysis

AdBoost uses **chi-square significance testing**:

- **p < 0.05** → Result is statistically significant
- **confidence_level: 0.95** → 95% confidence required by default
- Minimum sample size enforced before declaring winner
- Handles unequal traffic splits

## 🔄 Optimization Loop

```
Campaign Created
      ↓
Creative Generation (AI)
      ↓
Performance Prediction
      ↓
A/B Experiment Launched
      ↓
Traffic Collection
      ↓
Statistical Analysis
      ↓
Winner Declared
      ↓
Pattern Extraction
      ↓
Recommendations Generated
      ↓
New Variants Generated  ← Loop back
```

## 🏭 Production Notes

- Replace in-memory store (`models/database.py`) with PostgreSQL/MongoDB
- Add real traffic routing instead of simulation
- Connect to actual ad platforms (Google Ads, Meta) via APIs
- Add authentication (JWT) for multi-tenant use
- Deploy predictions to a real ML model (fine-tuned on your ad data)
