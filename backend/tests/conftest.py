"""Pytest configuration and shared fixtures."""

import pytest


# Configure pytest-asyncio to use auto mode
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(autouse=True)
def reset_global_instances():
    """Reset global singleton instances between tests."""
    import app.core.rate_limiter as rate_limiter_module

    rate_limiter_module._rate_limiter = None
    yield
    rate_limiter_module._rate_limiter = None
