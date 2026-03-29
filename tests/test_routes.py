import csv
import json
import os

import pytest

import app as flask_app


class TestSetupRedirect:
    def test_redirects_to_setup_without_config(self, client_no_config):
        resp = client_no_config.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/setup" in resp.headers["Location"]

    def test_setup_page_accessible_without_config(self, client_no_config):
        resp = client_no_config.get("/setup")
        assert resp.status_code == 200


class TestSetupWizard:
    def test_setup_saves_config(self, client_no_config, tmp_data_dir):
        flask_app.DATA_DIR = str(tmp_data_dir)
        flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "config.json")
        resp = client_no_config.post("/setup", data={
            "language": "en",
            "currency": "CHF",
            "name_0": "Alice",
            "name_1": "Bob",
            "budget_enabled": "yes",
            "budget_amount": "500",
            "cat_key_0": "food", "cat_icon_0": "\U0001f354", "cat_de_0": "Essen", "cat_en_0": "Food",
        }, follow_redirects=False)
        assert resp.status_code == 302
        config = flask_app.load_config()
        assert config["names"] == ["Alice", "Bob"]
        assert config["currency"] == "CHF"
        assert config["budget_enabled"] is True

    def test_setup_rejects_empty_names(self, client_no_config, tmp_data_dir):
        flask_app.DATA_DIR = str(tmp_data_dir)
        flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "config.json")
        resp = client_no_config.post("/setup", data={
            "language": "en",
            "currency": "CHF",
            "budget_enabled": "no",
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Config should NOT have been saved
        assert flask_app.load_config() is None


class TestIndexPage:
    def test_index_shows_form(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"expense-form" in resp.data

    def test_index_shows_names(self, client):
        resp = client.get("/")
        assert b"Alice" in resp.data
        assert b"Bob" in resp.data


class TestAddExpense:
    def test_add_valid_expense(self, client):
        resp = client.post("/api/expense", data={
            "name": "Alice",
            "category": "food",
            "amount": "12.50",
            "date": "2026-03-27",
            "note": "Test lunch",
        }, follow_redirects=False)
        assert resp.status_code == 302
        expenses = flask_app.read_expenses()
        assert len(expenses) == 1
        assert expenses[0]["name"] == "Alice"
        assert expenses[0]["amount"] == "12.50"

    def test_add_expense_missing_name(self, client):
        resp = client.post("/api/expense", data={
            "name": "",
            "category": "food",
            "amount": "10.00",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert flask_app.read_expenses() == []

    def test_add_expense_missing_category(self, client):
        resp = client.post("/api/expense", data={
            "name": "Alice",
            "category": "",
            "amount": "10.00",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert flask_app.read_expenses() == []

    def test_add_expense_invalid_amount(self, client):
        resp = client.post("/api/expense", data={
            "name": "Alice",
            "category": "food",
            "amount": "abc",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert flask_app.read_expenses() == []

    def test_add_expense_negative_amount(self, client):
        resp = client.post("/api/expense", data={
            "name": "Alice",
            "category": "food",
            "amount": "-5.00",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert flask_app.read_expenses() == []


class TestHistory:
    def test_history_page(self, client, sample_expenses):
        resp = client.get("/history")
        assert resp.status_code == 200
        assert b"Alice" in resp.data

    def test_history_filter_by_name(self, client, sample_expenses):
        resp = client.get("/history?name=Bob")
        assert resp.status_code == 200
        assert b"Bob" in resp.data

    def test_history_filter_by_month(self, client, sample_expenses):
        resp = client.get("/history?month=2026-02")
        assert resp.status_code == 200

    def test_history_empty(self, client):
        resp = client.get("/history")
        assert resp.status_code == 200


class TestDeleteExpense:
    def test_delete_existing_expense(self, client, sample_expenses):
        resp = client.post("/api/delete/aaa11111", follow_redirects=False)
        assert resp.status_code == 302
        expenses = flask_app.read_expenses()
        assert all(e["id"] != "aaa11111" for e in expenses)

    def test_delete_nonexistent_expense(self, client, sample_expenses):
        resp = client.post("/api/delete/zzz99999", follow_redirects=False)
        assert resp.status_code == 302
        expenses = flask_app.read_expenses()
        assert len(expenses) == 5


class TestSummary:
    def test_summary_page(self, client, sample_expenses):
        resp = client.get("/summary?month=2026-03")
        assert resp.status_code == 200
        assert b"Alice" in resp.data

    def test_summary_empty_month(self, client, sample_expenses):
        resp = client.get("/summary?month=2026-01")
        assert resp.status_code == 200


class TestExport:
    def test_export_csv(self, client, sample_expenses):
        resp = client.get("/api/export")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv; charset=utf-8"
        assert b"aaa11111" in resp.data

    def test_export_no_data(self, client):
        resp = client.get("/api/export", follow_redirects=True)
        assert resp.status_code == 200


class TestLanguageSwitch:
    def test_switch_to_en(self, client):
        resp = client.post("/api/lang/en", follow_redirects=False)
        assert resp.status_code == 302
        config = flask_app.load_config()
        assert config["language"] == "en"

    def test_switch_to_de(self, client):
        resp = client.post("/api/lang/de", follow_redirects=False)
        assert resp.status_code == 302
        config = flask_app.load_config()
        assert config["language"] == "de"

    def test_switch_invalid_lang_defaults_de(self, client):
        resp = client.post("/api/lang/fr", follow_redirects=False)
        assert resp.status_code == 302
        config = flask_app.load_config()
        assert config["language"] == "de"
