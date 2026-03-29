import csv
import json
import os
import threading
import uuid
from collections import defaultdict
from datetime import datetime, date

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    send_file, jsonify
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
CSV_FILE = os.path.join(DATA_DIR, "expenses.csv")
CSV_FIELDS = ["id", "timestamp", "date", "name", "category", "amount", "note"]

csv_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Default categories
# ---------------------------------------------------------------------------
DEFAULT_CATEGORIES = [
    {"key": "food", "icon": "\U0001f354", "de": "Essen & Trinken", "en": "Food & Drinks"},
    {"key": "clothing", "icon": "\U0001f455", "de": "Kleidung & Schuhe", "en": "Clothing & Shoes"},
    {"key": "cosmetics", "icon": "\U0001f9f4", "de": "K\u00f6rperpflege", "en": "Personal Care"},
    {"key": "mobile", "icon": "\U0001f4f1", "de": "Handy & Abos", "en": "Phone & Subscriptions"},
    {"key": "transport", "icon": "\U0001f68c", "de": "Verkehr", "en": "Transport"},
    {"key": "leisure", "icon": "\U0001f389", "de": "Freizeit & Ausgang", "en": "Leisure & Going Out"},
    {"key": "school", "icon": "\U0001f4da", "de": "Schule & B\u00fccher", "en": "School & Books"},
    {"key": "other", "icon": "\U0001f4e6", "de": "Sonstiges", "en": "Other"},
]

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
TRANSLATIONS = {
    "de": {
        "app_title": "Jugendlohn Tracker",
        "nav_entry": "Eintrag",
        "nav_history": "Verlauf",
        "nav_summary": "\u00dcbersicht",
        "nav_settings": "Einstellungen",
        "date": "Datum",
        "name": "Name",
        "category": "Kategorie",
        "amount": "Betrag",
        "note": "Notiz",
        "note_placeholder": "Optionale Notiz...",
        "save": "Speichern",
        "saved": "Gespeichert!",
        "delete": "L\u00f6schen",
        "delete_confirm": "Wirklich l\u00f6schen?",
        "deleted": "Gel\u00f6scht!",
        "export": "CSV exportieren",
        "filter_all": "Alle",
        "filter_month": "Monat",
        "no_expenses": "Noch keine Ausgaben erfasst.",
        "total": "Total",
        "budget": "Budget",
        "remaining": "Verbleibend",
        "over_budget": "\u00dcber Budget",
        "monthly_summary": "Monats\u00fcbersicht",
        "per_category": "Nach Kategorie",
        "setup_title": "Einrichtung",
        "setup_welcome": "Willkommen beim Jugendlohn Tracker!",
        "setup_language": "Sprache",
        "setup_names": "Namen der Kinder",
        "setup_names_help": "Einen Namen pro Zeile eingeben",
        "setup_currency": "W\u00e4hrung",
        "setup_budget_enable": "Monatsbudget aktivieren?",
        "setup_budget_amount": "Budget pro Person",
        "setup_categories": "Kategorien",
        "setup_save": "Einrichtung abschliessen",
        "add_name": "Name hinzuf\u00fcgen",
        "remove": "Entfernen",
        "yes": "Ja",
        "no": "Nein",
        "validation_name": "Bitte einen Namen w\u00e4hlen.",
        "validation_category": "Bitte eine Kategorie w\u00e4hlen.",
        "validation_amount": "Bitte einen g\u00fcltigen Betrag eingeben.",
        "validation_names_empty": "Bitte mindestens einen Namen eingeben.",
    },
    "en": {
        "app_title": "Jugendlohn Tracker",
        "nav_entry": "Entry",
        "nav_history": "History",
        "nav_summary": "Summary",
        "nav_settings": "Settings",
        "date": "Date",
        "name": "Name",
        "category": "Category",
        "amount": "Amount",
        "note": "Note",
        "note_placeholder": "Optional note...",
        "save": "Save",
        "saved": "Saved!",
        "delete": "Delete",
        "delete_confirm": "Really delete?",
        "deleted": "Deleted!",
        "export": "Export CSV",
        "filter_all": "All",
        "filter_month": "Month",
        "no_expenses": "No expenses recorded yet.",
        "total": "Total",
        "budget": "Budget",
        "remaining": "Remaining",
        "over_budget": "Over budget",
        "monthly_summary": "Monthly Summary",
        "per_category": "By Category",
        "setup_title": "Setup",
        "setup_welcome": "Welcome to Jugendlohn Tracker!",
        "setup_language": "Language",
        "setup_names": "Children\u2019s Names",
        "setup_names_help": "Enter one name per line",
        "setup_currency": "Currency",
        "setup_budget_enable": "Enable monthly budget?",
        "setup_budget_amount": "Budget per person",
        "setup_categories": "Categories",
        "setup_save": "Finish Setup",
        "add_name": "Add name",
        "remove": "Remove",
        "yes": "Yes",
        "no": "No",
        "validation_name": "Please select a name.",
        "validation_category": "Please select a category.",
        "validation_amount": "Please enter a valid amount.",
        "validation_names_empty": "Please enter at least one name.",
    },
}

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config():
    """Load config from JSON file. Returns None if not found."""
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    """Save config to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_lang(config=None):
    """Get current language from config, default 'de'."""
    if config is None:
        config = load_config()
    if config:
        return config.get("language", "de")
    return "de"


def t(key, config=None):
    """Translate a key using current language."""
    lang = get_lang(config)
    return TRANSLATIONS.get(lang, TRANSLATIONS["de"]).get(key, key)


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def sanitize_csv_field(value):
    """Strip leading formula-injection characters from a string value."""
    if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@"):
        return "'" + value
    return value


def read_expenses():
    """Read all expenses from CSV. Returns list of dicts."""
    with csv_lock:
        if not os.path.exists(CSV_FILE):
            return []
        with open(CSV_FILE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)


def write_expense(expense_dict):
    """Append a single expense row to CSV."""
    with csv_lock:
        os.makedirs(DATA_DIR, exist_ok=True)
        file_exists = os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0
        with open(CSV_FILE, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(expense_dict)


def delete_expense(expense_id):
    """Delete an expense by ID. Returns True if found and deleted."""
    with csv_lock:
        if not os.path.exists(CSV_FILE):
            return False
        with open(CSV_FILE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        original_len = len(rows)
        rows = [r for r in rows if r.get("id") != expense_id]
        if len(rows) == original_len:
            return False
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return True


def compute_summary(expenses, year_month):
    """Compute summary for a given YYYY-MM month string.

    Returns dict with keys: by_name, by_category, total, month_str
    Each by_name entry has: total, by_category dict
    """
    filtered = [e for e in expenses if e.get("date", "")[:7] == year_month]

    by_name = defaultdict(lambda: {"total": 0.0, "by_category": defaultdict(float)})
    by_category = defaultdict(float)
    total = 0.0

    for e in filtered:
        amount = float(e.get("amount", 0))
        name = e.get("name", "")
        cat = e.get("category", "")
        by_name[name]["total"] += amount
        by_name[name]["by_category"][cat] += amount
        by_category[cat] += amount
        total += amount

    # Convert defaultdicts to regular dicts for template use
    by_name = {
        k: {"total": v["total"], "by_category": dict(v["by_category"])}
        for k, v in by_name.items()
    }

    return {
        "by_name": by_name,
        "by_category": dict(by_category),
        "total": total,
        "month_str": year_month,
    }


# ---------------------------------------------------------------------------
# Template context
# ---------------------------------------------------------------------------

@app.context_processor
def inject_globals():
    config = load_config()
    lang = get_lang(config)

    def translate(key):
        return TRANSLATIONS.get(lang, TRANSLATIONS["de"]).get(key, key)

    def cat_label(cat_key):
        """Get category label in current language."""
        if config and "categories" in config:
            for cat in config["categories"]:
                if cat["key"] == cat_key:
                    return cat.get(lang, cat.get("de", cat_key))
        for cat in DEFAULT_CATEGORIES:
            if cat["key"] == cat_key:
                return cat.get(lang, cat_key)
        return cat_key

    def cat_icon(cat_key):
        """Get category emoji icon."""
        if config and "categories" in config:
            for cat in config["categories"]:
                if cat["key"] == cat_key:
                    return cat.get("icon", "")
        for cat in DEFAULT_CATEGORIES:
            if cat["key"] == cat_key:
                return cat.get("icon", "")
        return ""

    return {
        "t": translate,
        "cat_label": cat_label,
        "cat_icon": cat_icon,
        "config": config,
        "lang": lang,
        "today": date.today().isoformat(),
    }


# ---------------------------------------------------------------------------
# Before request: redirect to setup if no config
# ---------------------------------------------------------------------------

@app.before_request
def check_setup():
    if request.endpoint and request.endpoint in ("setup", "static"):
        return
    if load_config() is None:
        return redirect(url_for("setup"))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    config = load_config()
    return render_template("index.html")


@app.route("/api/expense", methods=["POST"])
def add_expense():
    config = load_config()
    lang = get_lang(config)

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    amount_str = request.form.get("amount", "").strip()
    expense_date = request.form.get("date", date.today().isoformat())
    note = request.form.get("note", "").strip()

    # Validation
    errors = []
    if not name:
        errors.append(t("validation_name", config))
    if not category:
        errors.append(t("validation_category", config))

    amount = None
    try:
        amount = round(float(amount_str), 2)
        if amount <= 0:
            errors.append(t("validation_amount", config))
    except (ValueError, TypeError):
        errors.append(t("validation_amount", config))

    if errors:
        for err in errors:
            flash(err, "error")
        return redirect(url_for("index"))

    expense = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "date": expense_date,
        "name": name,
        "category": category,
        "amount": f"{amount:.2f}",
        "note": sanitize_csv_field(note),
    }
    write_expense(expense)
    flash(t("saved", config), "success")
    return redirect(url_for("index"))


@app.route("/history")
def history():
    config = load_config()
    expenses = read_expenses()

    # Filter by name
    filter_name = request.args.get("name", "")
    # Filter by month
    filter_month = request.args.get("month", "")

    if filter_name:
        expenses = [e for e in expenses if e.get("name") == filter_name]
    if filter_month:
        expenses = [e for e in expenses if e.get("date", "")[:7] == filter_month]

    # Sort newest first
    expenses.sort(key=lambda e: e.get("date", ""), reverse=True)

    # Get available months for filter
    all_expenses = read_expenses()
    months = sorted(set(e.get("date", "")[:7] for e in all_expenses if e.get("date")), reverse=True)

    return render_template(
        "history.html",
        expenses=expenses,
        months=months,
        filter_name=filter_name,
        filter_month=filter_month,
    )


@app.route("/summary")
def summary():
    config = load_config()
    expenses = read_expenses()

    # Default to current month
    month = request.args.get("month", date.today().isoformat()[:7])

    summary_data = compute_summary(expenses, month)

    # Get available months
    months = sorted(set(e.get("date", "")[:7] for e in expenses if e.get("date")), reverse=True)
    if month not in months and months:
        pass  # keep requested month even if no data

    return render_template(
        "summary.html",
        summary=summary_data,
        months=months,
        current_month=month,
    )


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        language = request.form.get("language", "de")
        currency = request.form.get("currency", "CHF").strip()

        # Collect names
        names = []
        for key, val in request.form.items():
            if key.startswith("name_") and val.strip():
                names.append(val.strip())
        if not names:
            flash(
                TRANSLATIONS.get(language, TRANSLATIONS["de"]).get(
                    "validation_names_empty", "Please enter at least one name."
                ),
                "error",
            )
            return redirect(url_for("setup"))

        # Budget
        budget_enabled = request.form.get("budget_enabled") == "yes"
        budget_amount = 0
        if budget_enabled:
            try:
                budget_amount = round(float(request.form.get("budget_amount", "0")), 2)
            except (ValueError, TypeError):
                budget_amount = 0

        # Categories
        categories = []
        for i in range(8):
            key = request.form.get(f"cat_key_{i}", "")
            icon = request.form.get(f"cat_icon_{i}", "")
            de = request.form.get(f"cat_de_{i}", "")
            en = request.form.get(f"cat_en_{i}", "")
            if key:
                categories.append({"key": key, "icon": icon, "de": de, "en": en})

        if not categories:
            categories = DEFAULT_CATEGORIES[:]

        config = {
            "language": language,
            "currency": currency,
            "names": names,
            "budget_enabled": budget_enabled,
            "budget_amount": budget_amount,
            "categories": categories,
        }
        save_config(config)
        return redirect(url_for("index"))

    # GET
    config = load_config()
    return render_template(
        "setup.html",
        existing_config=config,
        default_categories=DEFAULT_CATEGORIES,
    )


@app.route("/api/delete/<expense_id>", methods=["POST"])
def delete(expense_id):
    config = load_config()
    if delete_expense(expense_id):
        flash(t("deleted", config), "success")
    return redirect(url_for("history"))


@app.route("/api/export")
def export():
    if not os.path.exists(CSV_FILE):
        flash("No data to export.", "error")
        return redirect(url_for("history"))
    return send_file(
        CSV_FILE,
        mimetype="text/csv",
        as_attachment=True,
        download_name="jugendlohn_expenses.csv",
    )


@app.route("/api/lang/<lang>", methods=["POST"])
def switch_lang(lang):
    if lang not in ("de", "en"):
        lang = "de"
    config = load_config()
    if config:
        config["language"] = lang
        save_config(config)
    return redirect(request.referrer or url_for("index"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        exclude_patterns=["tests/*"],
    )
