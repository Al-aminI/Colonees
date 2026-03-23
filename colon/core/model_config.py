"""
Centralized Model Configuration for Colonees Platform
Configures the AI model provider for all Strands agents
"""

import os
from strands.models.openai import OpenAIModel


def get_model():
    """
    Get configured model for all Colonees agents.
    Supports any OpenAI-compatible API provider (Groq, Fireworks, OpenAI, etc.)
    Configure via environment variables:
      LLM_API_KEY    — your provider API key
      LLM_BASE_URL   — provider base URL (default: Groq)
      LLM_MODEL_ID   — model identifier (default: moonshotai/kimi-k2-instruct-0905)
    """
    model = OpenAIModel(
        client_args={
            "api_key": os.getenv("LLM_API_KEY", ""),
            "base_url": os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
        },
        model_id=os.getenv("LLM_MODEL_ID", "moonshotai/kimi-k2-instruct-0905"),
        params={
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "16384")),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7"))
        }
    )
    return model
