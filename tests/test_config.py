import json
import os

import pytest

import app as flask_app


class TestConfigLoadSave:
    def test_load_config_missing_file(self, tmp_data_dir):
        flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "config.json")
        assert flask_app.load_config() is None

    def test_save_and_load_config(self, tmp_data_dir):
        flask_app.DATA_DIR = str(tmp_data_dir)
        flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "config.json")
        config = {"language": "de", "names": ["Test"], "currency": "EUR"}
        flask_app.save_config(config)
        loaded = flask_app.load_config()
        assert loaded["language"] == "de"
        assert loaded["names"] == ["Test"]
        assert loaded["currency"] == "EUR"

    def test_save_config_creates_data_dir(self, tmp_path):
        new_dir = os.path.join(str(tmp_path), "subdir")
        flask_app.DATA_DIR = new_dir
        flask_app.CONFIG_FILE = os.path.join(new_dir, "config.json")
        flask_app.save_config({"language": "en"})
        assert os.path.exists(flask_app.CONFIG_FILE)

    def test_update_config(self, tmp_data_dir):
        flask_app.DATA_DIR = str(tmp_data_dir)
        flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "config.json")
        flask_app.save_config({"language": "de", "names": ["A"]})
        config = flask_app.load_config()
        config["language"] = "en"
        flask_app.save_config(config)
        updated = flask_app.load_config()
        assert updated["language"] == "en"
        assert updated["names"] == ["A"]


class TestGetLang:
    def test_default_language(self, tmp_data_dir):
        flask_app.CONFIG_FILE = os.path.join(str(tmp_data_dir), "nonexistent.json")
        assert flask_app.get_lang(None) == "de"

    def test_language_from_config(self):
        assert flask_app.get_lang({"language": "en"}) == "en"

    def test_missing_language_key(self):
        assert flask_app.get_lang({}) == "de"


class TestTranslate:
    def test_translate_de(self):
        config = {"language": "de"}
        assert flask_app.t("save", config) == "Speichern"

    def test_translate_en(self):
        config = {"language": "en"}
        assert flask_app.t("save", config) == "Save"

    def test_translate_missing_key(self):
        config = {"language": "en"}
        assert flask_app.t("nonexistent_key", config) == "nonexistent_key"
