import csv
import os

import pytest

import app as flask_app


@pytest.fixture(autouse=True)
def setup_paths(tmp_data_dir):
    flask_app.DATA_DIR = str(tmp_data_dir)
    flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "config.json")
    flask_app.CSV_FILE = os.path.join(str(tmp_data_dir), "expenses.csv")


class TestReadExpenses:
    def test_read_empty_no_file(self):
        assert flask_app.read_expenses() == []

    def test_read_with_data(self, sample_expenses):
        expenses = flask_app.read_expenses()
        assert len(expenses) == 5
        assert expenses[0]["id"] == "aaa11111"
        assert expenses[0]["name"] == "Alice"

    def test_read_preserves_all_fields(self, sample_expenses):
        expenses = flask_app.read_expenses()
        for e in expenses:
            assert "id" in e
            assert "timestamp" in e
            assert "date" in e
            assert "name" in e
            assert "category" in e
            assert "amount" in e
            assert "note" in e


class TestWriteExpense:
    def test_write_creates_file_with_header(self):
        expense = {
            "id": "test0001",
            "timestamp": "2026-01-01T12:00:00",
            "date": "2026-01-01",
            "name": "Test",
            "category": "food",
            "amount": "10.00",
            "note": "",
        }
        flask_app.write_expense(expense)
        expenses = flask_app.read_expenses()
        assert len(expenses) == 1
        assert expenses[0]["id"] == "test0001"
        assert expenses[0]["amount"] == "10.00"

    def test_write_appends(self):
        for i in range(3):
            flask_app.write_expense({
                "id": f"test{i:04d}",
                "timestamp": "2026-01-01T12:00:00",
                "date": "2026-01-01",
                "name": "Test",
                "category": "food",
                "amount": f"{i + 1:.2f}",
                "note": "",
            })
        expenses = flask_app.read_expenses()
        assert len(expenses) == 3

    def test_write_amount_two_decimals(self):
        flask_app.write_expense({
            "id": "dec00001",
            "timestamp": "2026-01-01T12:00:00",
            "date": "2026-01-01",
            "name": "Test",
            "category": "food",
            "amount": "12.50",
            "note": "",
        })
        expenses = flask_app.read_expenses()
        assert expenses[0]["amount"] == "12.50"

    def test_write_special_characters_in_note(self):
        flask_app.write_expense({
            "id": "spec0001",
            "timestamp": "2026-01-01T12:00:00",
            "date": "2026-01-01",
            "name": "Test",
            "category": "food",
            "amount": "5.00",
            "note": "Caf\u00e9, Br\u00f6tchen & Z\u00fcrich",
        })
        expenses = flask_app.read_expenses()
        assert "Caf\u00e9" in expenses[0]["note"]
        assert "Z\u00fcrich" in expenses[0]["note"]


class TestDeleteExpense:
    def test_delete_existing(self, sample_expenses):
        result = flask_app.delete_expense("aaa11111")
        assert result is True
        expenses = flask_app.read_expenses()
        assert len(expenses) == 4
        assert all(e["id"] != "aaa11111" for e in expenses)

    def test_delete_nonexistent(self, sample_expenses):
        result = flask_app.delete_expense("zzz99999")
        assert result is False
        expenses = flask_app.read_expenses()
        assert len(expenses) == 5

    def test_delete_from_empty(self):
        result = flask_app.delete_expense("anything")
        assert result is False


class TestSanitizeCsvField:
    def test_normal_string(self):
        assert flask_app.sanitize_csv_field("hello") == "hello"

    def test_formula_injection_equals(self):
        assert flask_app.sanitize_csv_field("=SUM(A1)") == "'=SUM(A1)"

    def test_formula_injection_plus(self):
        assert flask_app.sanitize_csv_field("+cmd") == "'+cmd"

    def test_formula_injection_minus(self):
        assert flask_app.sanitize_csv_field("-cmd") == "'-cmd"

    def test_formula_injection_at(self):
        assert flask_app.sanitize_csv_field("@import") == "'@import"

    def test_empty_string(self):
        assert flask_app.sanitize_csv_field("") == ""

    def test_non_string(self):
        assert flask_app.sanitize_csv_field(42) == 42
