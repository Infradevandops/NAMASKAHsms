"""Integration test configuration."""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring a real PostgreSQL/Redis instance"
    )
