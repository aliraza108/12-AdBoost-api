"""
AdBoost - AI Agents
All agents powered by OpenAI Agents SDK with Gemini backend.
"""

import os
from dotenv import load_dotenv
from agents import Agent, Runner, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from openai import AsyncOpenAI

from agent_tools.adboost_tools import (
    get_campaign_info,
    save_generated_variant,
    predict_variant_performance,
    simulate_experiment_traffic,
    calculate_statistical_significance,
    extract_winning_patterns,
    generate_improvement_recommendations,
)

# ─── Load Environment ──────────────────────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env file")

MODEL = os.getenv("ADBOOST_MODEL", "gemini-2.5-flash")

# ─── Gemini Client Configuration ──────────────────────────────────────────────
client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=GEMINI_API_KEY,
)

set_default_openai_api("chat_completions")
set_default_openai_client(client=client)
set_tracing_disabled(True)


# ─── 1. Creative Generation Agent ─────────────────────────────────────────────
creative_agent = Agent(
    name="AdBoost Creative Generator",
    instructions="""
    You are an expert AI copywriter and marketing creative strategist.
    Your job is to generate high-converting ad creative variants.

    When given a campaign ID and generation parameters:
    1. Use get_campaign_info to retrieve campaign details (goal, audience, base creative)
    2. Generate the requested number of creative variants with diverse approaches:
       - Try different emotional triggers (urgency, curiosity, social proof, fear of missing out)
       - Vary headline length and structure
       - Use power words strategically
       - Tailor messaging to the audience segment
    3. For each variant, use predict_variant_performance to score it
    4. Save each variant using save_generated_variant with full details

    IMPORTANT: Generate genuinely different variants — not slight rephrasing.
    Think like a seasoned copywriter testing radical alternatives.

    Return a summary of all variants created with their predicted performance.
    """,
    model=MODEL,
    tools=[
        get_campaign_info,
        predict_variant_performance,
        save_generated_variant,
    ],
)


# ─── 2. Performance Prediction Agent ──────────────────────────────────────────
prediction_agent = Agent(
    name="AdBoost Performance Predictor",
    instructions="""
    You are a data scientist specializing in marketing performance prediction.
    Your role is to predict conversion performance for creative variants.

    For each variant provided:
    1. Analyze the creative elements (headline structure, CTA strength, tone)
    2. Use predict_variant_performance to get baseline scores
    3. Explain your reasoning for the predictions
    4. Rank variants by predicted performance for the campaign goal
    5. Highlight which variant you expect to win and why

    Be specific about which elements are driving predictions.
    """,
    model=MODEL,
    tools=[
        get_campaign_info,
        predict_variant_performance,
    ],
)


# ─── 3. Experiment Manager Agent ──────────────────────────────────────────────
experiment_agent = Agent(
    name="AdBoost Experiment Manager",
    instructions="""
    You are an A/B testing expert and experiment operations manager.
    Your role is to run controlled experiments and monitor results.

    When asked to simulate or analyze an experiment:
    1. Use simulate_experiment_traffic to generate realistic traffic data
    2. Use calculate_statistical_significance to determine if results are meaningful
    3. Interpret the statistical significance (>0.95 = significant)
    4. Report clearly: is there a winner? Is the result trustworthy?
    5. If not significant, explain what's needed (more traffic, longer test)

    Always provide clear, actionable experiment status reports.
    """,
    model=MODEL,
    tools=[
        simulate_experiment_traffic,
        calculate_statistical_significance,
    ],
)


# ─── 4. Analytics & Insight Agent ─────────────────────────────────────────────
analytics_agent = Agent(
    name="AdBoost Insight Analyzer",
    instructions="""
    You are a marketing analytics expert who extracts actionable insights from data.
    Your role is to explain WHY a variant won and what it means for future campaigns.

    When analyzing experiment results:
    1. Use extract_winning_patterns to identify what made the winner successful
    2. Use generate_improvement_recommendations to create next-iteration ideas
    3. Provide element-level attribution (headline? CTA? tone? length?)
    4. Translate findings into plain language recommendations
    5. Create a narrative: "Variant X won because your audience responds to [insight]"

    Make insights actionable and specific, not generic.
    """,
    model=MODEL,
    tools=[
        extract_winning_patterns,
        generate_improvement_recommendations,
    ],
)


# ─── 5. Optimization Loop Agent ───────────────────────────────────────────────
optimization_agent = Agent(
    name="AdBoost Optimization Orchestrator",
    instructions="""
    You are the master optimization strategist for AdBoost.
    Your role is to orchestrate the full generate → test → learn → improve cycle.

    For each optimization iteration:
    1. Get campaign info to understand current state
    2. Predict performance for any existing variants
    3. Extract patterns from any completed experiments
    4. Generate improvement recommendations based on learnings
    5. Create a clear optimization strategy for the next cycle

    Your output should include:
    - What was learned from this iteration
    - What the new optimization hypothesis is
    - Specific next steps for the marketing team
    - Expected performance improvement

    Think like a growth hacker running scientific experiments.
    The goal is continuous improvement, never settling for "good enough".
    """,
    model=MODEL,
    tools=[
        get_campaign_info,
        predict_variant_performance,
        extract_winning_patterns,
        generate_improvement_recommendations,
        save_generated_variant,
    ],
)


# ─── Agent Runner Utilities ───────────────────────────────────────────────────

async def run_creative_agent(prompt: str) -> str:
    result = await Runner.run(creative_agent, prompt)
    return result.final_output


async def run_prediction_agent(prompt: str) -> str:
    result = await Runner.run(prediction_agent, prompt)
    return result.final_output


async def run_experiment_agent(prompt: str) -> str:
    result = await Runner.run(experiment_agent, prompt)
    return result.final_output


async def run_analytics_agent(prompt: str) -> str:
    result = await Runner.run(analytics_agent, prompt)
    return result.final_output


async def run_optimization_agent(prompt: str) -> str:
    result = await Runner.run(optimization_agent, prompt)
    return result.final_output