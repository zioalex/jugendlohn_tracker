import pytest

import app as flask_app
from tests.conftest import SAMPLE_EXPENSES


class TestComputeSummary:
    def test_march_totals(self):
        summary = flask_app.compute_summary(SAMPLE_EXPENSES, "2026-03")
        assert summary["total"] == pytest.approx(63.10)
        assert "Alice" in summary["by_name"]
        assert "Bob" in summary["by_name"]
        assert summary["by_name"]["Alice"]["total"] == pytest.approx(18.10)
        assert summary["by_name"]["Bob"]["total"] == pytest.approx(45.00)

    def test_february_totals(self):
        summary = flask_app.compute_summary(SAMPLE_EXPENSES, "2026-02")
        assert summary["total"] == pytest.approx(38.00)
        assert summary["by_name"]["Alice"]["total"] == pytest.approx(8.00)
        assert summary["by_name"]["Bob"]["total"] == pytest.approx(30.00)

    def test_category_breakdown_march(self):
        summary = flask_app.compute_summary(SAMPLE_EXPENSES, "2026-03")
        assert summary["by_category"]["food"] == pytest.approx(12.50)
        assert summary["by_category"]["clothing"] == pytest.approx(45.00)
        assert summary["by_category"]["transport"] == pytest.approx(5.60)

    def test_per_name_category_breakdown(self):
        summary = flask_app.compute_summary(SAMPLE_EXPENSES, "2026-03")
        alice_cats = summary["by_name"]["Alice"]["by_category"]
        assert alice_cats["food"] == pytest.approx(12.50)
        assert alice_cats["transport"] == pytest.approx(5.60)

    def test_empty_month(self):
        summary = flask_app.compute_summary(SAMPLE_EXPENSES, "2026-01")
        assert summary["total"] == 0.0
        assert summary["by_name"] == {}
        assert summary["by_category"] == {}

    def test_empty_expenses_list(self):
        summary = flask_app.compute_summary([], "2026-03")
        assert summary["total"] == 0.0
        assert summary["by_name"] == {}

    def test_month_str_preserved(self):
        summary = flask_app.compute_summary(SAMPLE_EXPENSES, "2026-03")
        assert summary["month_str"] == "2026-03"
