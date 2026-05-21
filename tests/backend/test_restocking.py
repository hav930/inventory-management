"""
Tests for the Restocking feature: recommendations + submit + list.
"""
from datetime import datetime


class TestRestockingRecommendations:
    def test_zero_budget_returns_empty(self, client):
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200
        assert response.json() == []

    def test_sorted_by_shortage_desc(self, client):
        """With a generous budget, every actionable item appears and shortages descend."""
        response = client.get("/api/restocking/recommendations?budget=10000000")
        data = response.json()
        assert len(data) > 0
        shortages = [r["shortage"] for r in data]
        assert shortages == sorted(shortages, reverse=True)

    def test_budget_cap_respected(self, client):
        """sum(line_total) must not exceed the budget; partial fills are allowed."""
        budget = 50000
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        data = response.json()
        spent = sum(r["line_total"] for r in data)
        assert spent <= budget + 0.01  # rounding slack

    def test_recommendation_shape(self, client):
        data = client.get("/api/restocking/recommendations?budget=10000000").json()
        assert len(data) > 0
        rec = data[0]
        for field in (
            "sku", "name", "category", "warehouse", "quantity_on_hand",
            "forecasted_demand", "shortage", "suggested_quantity",
            "unit_cost", "line_total", "lead_time_days",
        ):
            assert field in rec, f"missing field: {field}"
        assert rec["shortage"] > 0
        assert rec["suggested_quantity"] > 0
        assert rec["lead_time_days"] > 0

    def test_partial_fill_when_budget_too_small_for_top_item(self, client):
        """Tiny budget should still buy *something* via a partial fill."""
        data = client.get("/api/restocking/recommendations?budget=500").json()
        assert len(data) >= 1
        first = data[0]
        # Partial fill: suggested_quantity < shortage but > 0
        assert 0 < first["suggested_quantity"] <= first["shortage"]
        assert first["line_total"] <= 500 + 0.01


class TestRestockingOrderSubmission:
    def _sample_payload(self, client):
        rec = client.get("/api/restocking/recommendations?budget=100000").json()[0]
        return {
            "budget": 100000,
            "items": [{
                "sku": rec["sku"],
                "name": rec["name"],
                "quantity": rec["suggested_quantity"],
                "unit_cost": rec["unit_cost"],
                "lead_time_days": rec["lead_time_days"],
                "line_total": rec["line_total"],
            }],
        }

    def test_submit_returns_populated_order(self, client):
        response = client.post("/api/restocking/orders", json=self._sample_payload(client))
        assert response.status_code == 200
        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["total_value"] > 0
        assert order["submitted_date"]
        assert order["expected_delivery"]
        assert len(order["items"]) == 1

    def test_expected_delivery_is_submitted_plus_max_lead_time(self, client):
        payload = self._sample_payload(client)
        # Force a multi-item scenario with different lead times
        payload["items"].append({
            "sku": "TEST-X", "name": "Test", "quantity": 1,
            "unit_cost": 1.0, "lead_time_days": 30, "line_total": 1.0,
        })
        order = client.post("/api/restocking/orders", json=payload).json()
        submitted = datetime.fromisoformat(order["submitted_date"])
        delivery = datetime.fromisoformat(order["expected_delivery"])
        delta_days = (delivery - submitted).days
        assert delta_days == 30  # max of [item1.lead_time_days, 30]

    def test_empty_items_rejected(self, client):
        response = client.post("/api/restocking/orders", json={"budget": 100, "items": []})
        assert response.status_code == 400

    def test_submitted_order_appears_in_list_newest_first(self, client):
        before = client.get("/api/restocking/orders").json()
        client.post("/api/restocking/orders", json=self._sample_payload(client))
        after = client.get("/api/restocking/orders").json()
        assert len(after) == len(before) + 1
        # Newest first
        if len(after) >= 2:
            first_date = datetime.fromisoformat(after[0]["submitted_date"])
            second_date = datetime.fromisoformat(after[1]["submitted_date"])
            assert first_date >= second_date
