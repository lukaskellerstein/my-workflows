"""Helper functions for creating and configuring LLMs and agents."""

from typing import Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel


def create_llm(
    provider: str = "anthropic",
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Create an LLM instance based on provider.

    Args:
        provider: LLM provider ('anthropic' or 'openai')
        model: Model name (uses defaults if not provided)
        temperature: Temperature for responses
        max_tokens: Maximum tokens in response
        **kwargs: Additional provider-specific arguments

    Returns:
        BaseChatModel: Configured LLM instance
    """
    if provider.lower() == "anthropic":
        return ChatAnthropic(
            model=model or "claude-sonnet-4-20250514",
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
    elif provider.lower() == "openai":
        return ChatOpenAI(
            model=model or "gpt-4o",
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
