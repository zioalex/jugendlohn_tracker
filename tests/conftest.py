import json
import csv
import os
import tempfile

import pytest

# Ensure app can be imported
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as flask_app


SAMPLE_CONFIG = {
    "language": "en",
    "currency": "CHF",
    "names": ["Alice", "Bob"],
    "budget_enabled": True,
    "budget_amount": 500.00,
    "categories": [
        {"key": "food", "icon": "\U0001f354", "de": "Essen & Trinken", "en": "Food & Drinks"},
        {"key": "clothing", "icon": "\U0001f455", "de": "Kleidung & Schuhe", "en": "Clothing & Shoes"},
        {"key": "cosmetics", "icon": "\U0001f9f4", "de": "K\u00f6rperpflege", "en": "Personal Care"},
        {"key": "mobile", "icon": "\U0001f4f1", "de": "Handy & Abos", "en": "Phone & Subscriptions"},
        {"key": "transport", "icon": "\U0001f68c", "de": "Verkehr", "en": "Transport"},
        {"key": "leisure", "icon": "\U0001f389", "de": "Freizeit & Ausgang", "en": "Leisure & Going Out"},
        {"key": "school", "icon": "\U0001f4da", "de": "Schule & B\u00fccher", "en": "School & Books"},
        {"key": "other", "icon": "\U0001f4e6", "de": "Sonstiges", "en": "Other"},
    ],
}

SAMPLE_EXPENSES = [
    {"id": "aaa11111", "timestamp": "2026-03-01T10:00:00", "date": "2026-03-01", "name": "Alice", "category": "food", "amount": "12.50", "note": "Lunch"},
    {"id": "aaa22222", "timestamp": "2026-03-05T14:00:00", "date": "2026-03-05", "name": "Bob", "category": "clothing", "amount": "45.00", "note": ""},
    {"id": "aaa33333", "timestamp": "2026-03-10T09:00:00", "date": "2026-03-10", "name": "Alice", "category": "transport", "amount": "5.60", "note": "Bus ticket"},
    {"id": "aaa44444", "timestamp": "2026-02-15T12:00:00", "date": "2026-02-15", "name": "Alice", "category": "food", "amount": "8.00", "note": ""},
    {"id": "aaa55555", "timestamp": "2026-02-20T16:00:00", "date": "2026-02-20", "name": "Bob", "category": "leisure", "amount": "30.00", "note": "Cinema"},
]


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory."""
    return tmp_path


@pytest.fixture
def sample_config(tmp_data_dir):
    """Write sample config.json to tmp_data_dir and return the config dict."""
    config_path = os.path.join(tmp_data_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_CONFIG, f, ensure_ascii=False)
    return SAMPLE_CONFIG


@pytest.fixture
def sample_expenses(tmp_data_dir):
    """Write sample expenses.csv to tmp_data_dir and return the list."""
    csv_path = os.path.join(tmp_data_dir, "expenses.csv")
    fields = ["id", "timestamp", "date", "name", "category", "amount", "note"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(SAMPLE_EXPENSES)
    return SAMPLE_EXPENSES


@pytest.fixture
def app_instance(tmp_data_dir, sample_config):
    """Create a Flask test app pointing to tmp_data_dir with config."""
    flask_app.DATA_DIR = str(tmp_data_dir)
    flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "config.json")
    flask_app.CSV_FILE = os.path.join(str(tmp_data_dir), "expenses.csv")
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["SECRET_KEY"] = "test-secret"
    return flask_app.app


@pytest.fixture
def client(app_instance):
    """Flask test client."""
    return app_instance.test_client()


@pytest.fixture
def client_no_config(tmp_data_dir):
    """Flask test client with NO config (first-run state)."""
    flask_app.DATA_DIR = str(tmp_data_dir)
    flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "config.json")
    flask_app.CSV_FILE = os.path.join(str(tmp_data_dir), "expenses.csv")
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["SECRET_KEY"] = "test-secret"
    return flask_app.app.test_client()
