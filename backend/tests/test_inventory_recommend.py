# backend/tests/test_inventory_recommend.py
"""
Comprehensive test coverage for the inventory recommendation endpoint
including coverage calculation, expiration scoring, and response formatting.
"""
import os
import sys
from datetime import datetime, timedelta

# ensure backend is on the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.recommender import (
    CoverageResult,
    calculate_coverage,
    calculate_expiration_urgency,
    combined_score,
)


class TestCoverageCalculation:
    """Tests for the calculate_coverage function."""

    def test_full_coverage(self, sample_recipe_ingredient_ids, matching_inventory):
        """100% coverage when all ingredients available."""
        result = calculate_coverage(sample_recipe_ingredient_ids, matching_inventory)
        assert result.score == 1.0
        assert len(result.missing) == 0
        assert isinstance(result, CoverageResult)

    def test_partial_coverage(self, sample_recipe_ingredient_ids, partial_inventory):
        """Partial coverage calculated correctly."""
        result = calculate_coverage(sample_recipe_ingredient_ids, partial_inventory)
        assert 0 < result.score < 1.0
        assert result.score == 0.5  # 2 out of 4 ingredients
        assert len(result.missing) > 0
        assert 4 in result.missing
        assert 5 in result.missing

    def test_no_coverage(self, sample_recipe_ingredient_ids, empty_inventory):
        """Zero coverage when no ingredients match."""
        result = calculate_coverage(sample_recipe_ingredient_ids, empty_inventory)
        assert result.score == 0.0
        assert len(result.missing) == len(sample_recipe_ingredient_ids)

    def test_empty_recipe_ingredients(self, sample_inventory):
        """Empty recipe ingredients should return full coverage."""
        result = calculate_coverage([], sample_inventory)
        assert result.score == 1.0
        assert len(result.missing) == 0

    def test_coverage_with_extra_inventory(self):
        """Coverage should not be affected by extra inventory items."""
        recipe_ids = [1, 2]
        inventory = [
            {"ingredient_id": 1, "quantity": 100},
            {"ingredient_id": 2, "quantity": 200},
            {"ingredient_id": 3, "quantity": 300},
            {"ingredient_id": 4, "quantity": 400},
        ]
        result = calculate_coverage(recipe_ids, inventory)
        assert result.score == 1.0
        assert len(result.missing) == 0

    def test_coverage_returns_correct_missing(self):
        """Verify missing ingredients are correctly identified."""
        recipe_ids = [1, 2, 3, 4, 5]
        inventory = [
            {"ingredient_id": 2, "quantity": 100},
            {"ingredient_id": 4, "quantity": 200},
        ]
        result = calculate_coverage(recipe_ids, inventory)
        assert result.score == 0.4  # 2 out of 5
        assert set(result.missing) == {1, 3, 5}


class TestExpirationUrgency:
    """Tests for the calculate_expiration_urgency function."""

    def test_expired_item(self):
        """Expired items have max urgency."""
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        urgency = calculate_expiration_urgency(past_date)
        assert urgency == 1.0

    def test_critical_expiration(self):
        """Items expiring in 1-2 days have high urgency."""
        soon_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        urgency = calculate_expiration_urgency(soon_date)
        assert urgency >= 0.8

    def test_expiring_tomorrow(self):
        """Items expiring tomorrow have very high urgency."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        urgency = calculate_expiration_urgency(tomorrow)
        assert urgency >= 0.8

    def test_expiring_in_week(self):
        """Items expiring in a week have moderate urgency."""
        week_later = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        urgency = calculate_expiration_urgency(week_later)
        assert 0.3 <= urgency <= 0.6

    def test_expiring_in_two_weeks(self):
        """Items expiring in two weeks have low urgency."""
        two_weeks = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        urgency = calculate_expiration_urgency(two_weeks)
        assert urgency <= 0.3

    def test_no_expiration_date(self):
        """Null expiration returns zero urgency."""
        assert calculate_expiration_urgency(None) == 0.0

    def test_invalid_date_format(self):
        """Invalid date format returns zero urgency."""
        assert calculate_expiration_urgency("not-a-date") == 0.0
        assert calculate_expiration_urgency("") == 0.0

    def test_far_future_expiration(self):
        """Items expiring far in the future have no urgency."""
        far_future = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        urgency = calculate_expiration_urgency(far_future)
        assert urgency == 0.0

    def test_iso_datetime_format(self):
        """ISO datetime format is handled correctly."""
        past_datetime = (datetime.now() - timedelta(days=1)).isoformat()
        urgency = calculate_expiration_urgency(past_datetime)
        assert urgency == 1.0


class TestCombinedScoring:
    """Tests for the combined_score function."""

    def test_high_coverage_high_expiration(self):
        """Combined score reflects both factors."""
        score = combined_score(coverage=0.9, expiration=0.8)
        # 0.9 * 0.7 + 0.8 * 0.3 = 0.63 + 0.24 = 0.87
        assert 0.8 < score < 0.9
        assert abs(score - 0.87) < 0.01

    def test_coverage_weighted_higher(self):
        """Coverage contributes more than expiration."""
        # Same scores should weight coverage higher
        high_cov = combined_score(coverage=0.9, expiration=0.5)
        high_exp = combined_score(coverage=0.5, expiration=0.9)
        assert high_cov > high_exp

    def test_perfect_coverage_zero_expiration(self):
        """Perfect coverage with no expiration urgency."""
        score = combined_score(coverage=1.0, expiration=0.0)
        assert score == 0.7  # 1.0 * 0.7 + 0.0 * 0.3

    def test_zero_coverage_perfect_expiration(self):
        """Zero coverage with high expiration urgency."""
        score = combined_score(coverage=0.0, expiration=1.0)
        assert score == 0.3  # 0.0 * 0.7 + 1.0 * 0.3

    def test_perfect_scores(self):
        """Both scores at maximum."""
        score = combined_score(coverage=1.0, expiration=1.0)
        assert score == 1.0

    def test_zero_scores(self):
        """Both scores at minimum."""
        score = combined_score(coverage=0.0, expiration=0.0)
        assert score == 0.0

    def test_balanced_scores(self):
        """Balanced scores produce expected result."""
        score = combined_score(coverage=0.5, expiration=0.5)
        assert score == 0.5  # 0.5 * 0.7 + 0.5 * 0.3 = 0.35 + 0.15


class TestInventoryRecommendEndpoint:
    """Tests for the /inventory-recommend endpoint."""

    def test_successful_recommendation(self, client, sample_inventory):
        """Endpoint returns recommendations for valid inventory."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": sample_inventory,
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert isinstance(data["recipes"], list)
        assert len(data["recipes"]) <= 5

    def test_empty_inventory(self, client):
        """Endpoint handles empty inventory gracefully."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": [],
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recipes"] == []

    def test_default_num_recipes(self, client, sample_inventory):
        """Endpoint uses default num_recipes when not specified."""
        response = client.post(
            "/inventory-recommend",
            json={"inventory": sample_inventory},
        )
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data

    def test_invalid_num_recipes_too_high(self, client, sample_inventory):
        """Endpoint rejects num_recipes above limit."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": sample_inventory,
                "num_recipes": 100,
            },
        )
        assert response.status_code == 422

    def test_invalid_num_recipes_zero(self, client, sample_inventory):
        """Endpoint rejects zero num_recipes."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": sample_inventory,
                "num_recipes": 0,
            },
        )
        assert response.status_code == 422

    def test_invalid_inventory_format(self, client):
        """Endpoint rejects invalid inventory format."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": "not a list",
                "num_recipes": 5,
            },
        )
        assert response.status_code == 422

    def test_missing_required_field(self, client):
        """Endpoint requires inventory field."""
        response = client.post(
            "/inventory-recommend",
            json={"num_recipes": 5},
        )
        assert response.status_code == 422


class TestResponseFormat:
    """Tests for response format and structure."""

    def test_recipe_structure(self, client, sample_inventory):
        """Each recipe in response should have expected fields."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": sample_inventory,
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()

        for recipe in data["recipes"]:
            assert "recipe_id" in recipe
            assert "name" in recipe
            assert "coverage_score" in recipe
            assert "expiration_urgency" in recipe
            assert "combined_score" in recipe
            assert "missing_ingredients" in recipe

    def test_scores_are_valid(self, client, sample_inventory):
        """Scores should be valid floats between 0 and 1."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": sample_inventory,
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()

        for recipe in data["recipes"]:
            assert 0 <= recipe["coverage_score"] <= 1
            assert 0 <= recipe["expiration_urgency"] <= 1
            assert 0 <= recipe["combined_score"] <= 1

    def test_recipes_sorted_by_combined_score(self, client, sample_inventory):
        """Recipes should be sorted by combined score descending."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": sample_inventory,
                "num_recipes": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        recipes = data["recipes"]

        if len(recipes) > 1:
            scores = [r["combined_score"] for r in recipes]
            assert scores == sorted(scores, reverse=True)


class TestEdgeCases:
    """Edge case and robustness tests."""

    def test_single_inventory_item(self, client):
        """Single inventory item should work correctly."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": [{"ingredient_id": 1, "quantity": 100}],
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200

    def test_large_inventory(self, client):
        """Large inventory should not cause issues."""
        large_inventory = [
            {"ingredient_id": i, "quantity": 100} for i in range(1, 101)
        ]
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": large_inventory,
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200

    def test_inventory_with_all_expired_items(self, client):
        """Inventory with all expired items should still work."""
        past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        expired_inventory = [
            {"ingredient_id": 1, "quantity": 100, "expiration_date": past_date},
            {"ingredient_id": 2, "quantity": 200, "expiration_date": past_date},
        ]
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": expired_inventory,
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200

    def test_inventory_item_without_expiration(self, client):
        """Inventory items without expiration date should work."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": [
                    {"ingredient_id": 1, "quantity": 100},
                    {"ingredient_id": 2, "quantity": 200},
                ],
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200

    def test_num_recipes_equals_one(self, client, sample_inventory):
        """Request for single recipe should return at most one."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": sample_inventory,
                "num_recipes": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recipes"]) <= 1

    def test_very_small_quantities(self, client):
        """Very small quantities should be handled."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": [
                    {"ingredient_id": 1, "quantity": 0.001},
                    {"ingredient_id": 2, "quantity": 0.0001},
                ],
                "num_recipes": 5,
            },
        )
        assert response.status_code == 200

    def test_negative_quantity_allowed(self, client):
        """Negative quantities should be handled gracefully."""
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": [{"ingredient_id": 1, "quantity": -100}],
                "num_recipes": 5,
            },
        )
        # Negative quantities might be allowed or rejected depending on business rules
        assert response.status_code in [200, 422]


class TestPerformance:
    """Performance tests for the inventory recommendation endpoint."""

    def test_reasonable_response_time_small_inventory(self, client):
        """Small inventory should return quickly."""
        import time

        small_inventory = [
            {"ingredient_id": i, "quantity": 100} for i in range(1, 6)
        ]
        start = time.time()
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": small_inventory,
                "num_recipes": 5,
            },
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30

    def test_reasonable_response_time_medium_inventory(self, client):
        """Medium inventory should return in reasonable time."""
        import time

        medium_inventory = [
            {"ingredient_id": i, "quantity": 100} for i in range(1, 26)
        ]
        start = time.time()
        response = client.post(
            "/inventory-recommend",
            json={
                "inventory": medium_inventory,
                "num_recipes": 10,
            },
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        # Should complete in reasonable time (< 60 seconds)
        assert elapsed < 60
