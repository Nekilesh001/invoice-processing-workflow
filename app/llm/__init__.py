"""
LLM Abstraction Layer Package.
Handles OpenAI-compatible client communication and prompt loading.
"""

from app.llm.client import LLMClient

__all__ = ["LLMClient"]
