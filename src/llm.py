"""Anthropic SDK client wrapper configured for DeepSeek proxy."""

from anthropic import Anthropic
from src.config import config


def create_client() -> Anthropic:
    return Anthropic(
        base_url=config.anthropic_base_url,
        api_key=config.anthropic_api_key,
    )


_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = create_client()
    return _client
