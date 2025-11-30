# backend/tests/test_inventory_recommend.py
"""Tests for inventory-based recipe recommendations."""

import pytest

from api.recommender import (
    calculate_days_until_expiration,
    generate_reasoning,
)

# --------------------------------------------------
# API Endpoint Tests
# --------------------------------------------------


def test_inventory_recommend_empty_inventory(client):
    """Empty inventory should return 400 error."""
    payload = {"inventory": []}
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_inventory_recommend_invalid_num_recipes(client):
    """Invalid numRecipes should return 400 error."""
    payload = {
        "inventory": [{"ingredient_id": 1, "quantity": 100}],
        "numRecipes": 25,  # Too high
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 400
    assert "numRecipes" in response.json()["detail"]


def test_inventory_recommend_invalid_num_recipes_zero(client):
    """numRecipes of 0 should return 400 error."""
    payload = {
        "inventory": [{"ingredient_id": 1, "quantity": 100}],
        "numRecipes": 0,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 400


def test_inventory_recommend_basic_structure(client):
    """Basic request should return proper response structure."""
    payload = {
        "inventory": [
            {"ingredient_id": 1, "quantity": 500},
            {"ingredient_id": 2, "quantity": 200},
        ],
        "numRecipes": 3,
    }
    response = client.post("/inventory-recommend", json=payload)
    # May return 200 with no recipes found, or recipes
    assert response.status_code == 200

    data = response.json()
    assert "recipes" in data
    assert "summary" in data
    assert isinstance(data["recipes"], list)
    assert isinstance(data["summary"], str)


def test_inventory_recommend_with_expiration(client):
    """Request with expiration dates should be accepted."""
    payload = {
        "inventory": [
            {
                "ingredient_id": 1,
                "quantity": 500,
                "expiration_date": "2025-12-05",
            },
            {"ingredient_id": 2, "quantity": 200},
        ],
        "numRecipes": 5,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "recipes" in data


def test_inventory_recommend_with_preferences(client):
    """Request with preferences should be accepted."""
    payload = {
        "inventory": [
            {"ingredient_id": 1, "quantity": 500},
        ],
        "preferences": "low carb",
        "numRecipes": 3,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200


def test_inventory_recommend_response_recipe_structure(client):
    """Each recipe in response should have required fields."""
    payload = {
        "inventory": [
            {"ingredient_id": 1, "quantity": 500},
            {"ingredient_id": 2, "quantity": 200},
            {"ingredient_id": 3, "quantity": 300},
        ],
        "numRecipes": 5,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200

    data = response.json()
    for recipe in data["recipes"]:
        assert "recipe_id" in recipe
        assert "recipe_name" in recipe
        assert "coverage_score" in recipe
        assert "missing_ingredients" in recipe
        assert "uses_expiring" in recipe
        assert "reasoning" in recipe
        # Validate types
        assert isinstance(recipe["recipe_id"], int)
        assert isinstance(recipe["recipe_name"], str)
        assert isinstance(recipe["coverage_score"], float)
        assert isinstance(recipe["missing_ingredients"], list)
        assert isinstance(recipe["uses_expiring"], list)
        assert isinstance(recipe["reasoning"], str)


def test_inventory_recommend_coverage_score_range(client):
    """Coverage scores should be between 0 and 1."""
    payload = {
        "inventory": [
            {"ingredient_id": 1, "quantity": 500},
            {"ingredient_id": 2, "quantity": 200},
        ],
        "numRecipes": 5,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200

    data = response.json()
    for recipe in data["recipes"]:
        assert 0 <= recipe["coverage_score"] <= 1.0


# --------------------------------------------------
# Parametrized Tests
# --------------------------------------------------


@pytest.mark.parametrize("num_recipes", [1, 3, 5, 10])
def test_inventory_recommend_various_counts(client, num_recipes):
    """Different numRecipes values should work."""
    payload = {
        "inventory": [
            {"ingredient_id": 1, "quantity": 500},
            {"ingredient_id": 2, "quantity": 200},
        ],
        "numRecipes": num_recipes,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["recipes"]) <= num_recipes


@pytest.mark.parametrize(
    "expiration_date",
    [
        "2025-12-01",
        "2025-12-15",
        "2026-01-01",
        None,  # No expiration
    ],
)
def test_inventory_recommend_various_expiration_dates(client, expiration_date):
    """Different expiration dates should be handled."""
    item = {"ingredient_id": 1, "quantity": 500}
    if expiration_date:
        item["expiration_date"] = expiration_date

    payload = {"inventory": [item], "numRecipes": 3}
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200


# --------------------------------------------------
# Edge Case Tests
# --------------------------------------------------


def test_inventory_recommend_single_ingredient(client):
    """Single ingredient should work."""
    payload = {
        "inventory": [{"ingredient_id": 1, "quantity": 500}],
        "numRecipes": 3,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200


def test_inventory_recommend_many_ingredients(client):
    """Many ingredients should work."""
    payload = {
        "inventory": [{"ingredient_id": i, "quantity": 100} for i in range(1, 20)],
        "numRecipes": 5,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200


def test_inventory_recommend_missing_quantity(client):
    """Missing quantity should be handled gracefully."""
    payload = {
        "inventory": [
            {"ingredient_id": 1},  # No quantity
        ],
        "numRecipes": 3,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200


def test_inventory_recommend_only_ingredient_id(client):
    """Only ingredient_id (minimal info) should work."""
    payload = {
        "inventory": [
            {"ingredient_id": 1},
            {"ingredient_id": 2},
        ],
        "numRecipes": 3,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 200


# --------------------------------------------------
# Validation Tests
# --------------------------------------------------


def test_inventory_recommend_invalid_json(client):
    """Invalid JSON should return 422."""
    response = client.post(
        "/inventory-recommend",
        content="not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_inventory_recommend_missing_inventory_field(client):
    """Missing inventory field should return 422."""
    payload = {"numRecipes": 5}
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 422


def test_inventory_recommend_missing_ingredient_id(client):
    """Items missing ingredient_id should return 422."""
    payload = {
        "inventory": [{"quantity": 500}],  # Missing ingredient_id
        "numRecipes": 3,
    }
    response = client.post("/inventory-recommend", json=payload)
    assert response.status_code == 422


# --------------------------------------------------
# Unit Tests for Recommender Functions
# --------------------------------------------------


class TestCalculateDaysUntilExpiration:
    """Tests for expiration date calculation."""

    def test_none_expiration(self):
        """None expiration date returns None."""
        assert calculate_days_until_expiration(None) is None

    def test_empty_string_expiration(self):
        """Empty string returns None."""
        assert calculate_days_until_expiration("") is None

    def test_invalid_date_format(self):
        """Invalid date format returns None."""
        assert calculate_days_until_expiration("not-a-date") is None

    def test_valid_date_format(self):
        """Valid ISO date returns integer."""
        from datetime import date, timedelta

        future_date = (date.today() + timedelta(days=5)).isoformat()
        result = calculate_days_until_expiration(future_date)
        assert result == 5

    def test_past_date(self):
        """Past date returns negative number."""
        from datetime import date, timedelta

        past_date = (date.today() - timedelta(days=3)).isoformat()
        result = calculate_days_until_expiration(past_date)
        assert result == -3

    def test_today(self):
        """Today's date returns 0."""
        from datetime import date

        today = date.today().isoformat()
        result = calculate_days_until_expiration(today)
        assert result == 0


class TestGenerateReasoning:
    """Tests for reasoning generation."""

    def test_full_coverage_no_expiring(self):
        """100% coverage with no expiring items."""
        reasoning = generate_reasoning(1.0, [], [])
        assert "all the ingredients" in reasoning.lower()

    def test_high_coverage_no_expiring(self):
        """High coverage with no expiring items."""
        reasoning = generate_reasoning(0.85, [], [])
        assert "85%" in reasoning

    def test_with_single_expiring(self):
        """Single expiring ingredient mentioned."""
        expiring = [{"name": "Chicken", "expires_in_days": 2}]
        reasoning = generate_reasoning(0.8, expiring, [])
        assert "chicken" in reasoning.lower()
        assert "expiring" in reasoning.lower()

    def test_with_multiple_expiring(self):
        """Multiple expiring ingredients mentioned."""
        expiring = [
            {"name": "Chicken", "expires_in_days": 2},
            {"name": "Milk", "expires_in_days": 1},
        ]
        reasoning = generate_reasoning(0.8, expiring, [])
        assert "expiring" in reasoning.lower()

    def test_with_missing_ingredients(self):
        """Missing ingredients mentioned."""
        missing = ["Salt", "Pepper"]
        reasoning = generate_reasoning(0.7, [], missing)
        assert "missing" in reasoning.lower()

    def test_with_many_missing(self):
        """Many missing ingredients shows count."""
        missing = ["Salt", "Pepper", "Onion", "Garlic", "Oil"]
        reasoning = generate_reasoning(0.5, [], missing)
        assert "5" in reasoning or "missing" in reasoning.lower()

    def test_combined_info(self):
        """Coverage, expiring, and missing all shown."""
        expiring = [{"name": "Beef", "expires_in_days": 1}]
        missing = ["Soy Sauce"]
        reasoning = generate_reasoning(0.75, expiring, missing)
        assert "75%" in reasoning
        assert "beef" in reasoning.lower()
        assert "missing" in reasoning.lower()
