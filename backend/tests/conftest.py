# backend/tests/conftest.py
import os
import sys
from datetime import datetime, timedelta

import pytest

# Set mock environment variables before any imports that need them
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_ANON_KEY", "test-key")
os.environ.setdefault("GEMINI_KEY", "test-gemini-key")

from fastapi.testclient import TestClient

# ensure backend is on the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.index import app


@pytest.fixture
def client():
    """Provides a FastAPI test client for all tests."""
    with TestClient(app) as c:
        yield c


# Inventory fixtures for test_inventory_recommend.py


@pytest.fixture
def sample_inventory():
    """Sample inventory with typical items."""
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    later_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    return [
        {"ingredient_id": 1, "quantity": 500, "expiration_date": future_date},
        {"ingredient_id": 2, "quantity": 200, "expiration_date": None},
        {"ingredient_id": 3, "quantity": 100, "expiration_date": later_date},
    ]


@pytest.fixture
def expiring_soon_inventory():
    """Inventory with items expiring very soon."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return [
        {"ingredient_id": 1, "quantity": 500, "expiration_date": tomorrow},
        {"ingredient_id": 2, "quantity": 200, "expiration_date": tomorrow},
    ]


@pytest.fixture
def empty_inventory():
    """Empty inventory list."""
    return []


@pytest.fixture
def matching_inventory():
    """Inventory that fully matches a sample recipe."""
    return [
        {"ingredient_id": 1, "quantity": 500, "expiration_date": None},
        {"ingredient_id": 2, "quantity": 200, "expiration_date": None},
        {"ingredient_id": 4, "quantity": 100, "expiration_date": None},
        {"ingredient_id": 5, "quantity": 150, "expiration_date": None},
    ]


@pytest.fixture
def partial_inventory():
    """Inventory that partially matches a sample recipe."""
    return [
        {"ingredient_id": 1, "quantity": 500, "expiration_date": None},
        {"ingredient_id": 2, "quantity": 200, "expiration_date": None},
    ]


@pytest.fixture
def sample_recipe_ingredient_ids():
    """Sample recipe ingredient IDs for testing coverage."""
    return [1, 2, 4, 5]
