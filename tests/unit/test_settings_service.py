"""Tests for SettingsService."""

import json
from pathlib import Path

from lazyclaude.models.settings import AppSettings
from lazyclaude.services.settings import SettingsService
from lazyclaude.themes import DEFAULT_THEME


class TestLoad:
    """Tests for load method."""

    def test_returns_defaults_when_file_not_exists(self, _fs, fake_home: Path) -> None:
        """Loading from non-existent file returns default settings."""
        settings_path = fake_home / ".lazyclaude" / "settings.json"
        service = SettingsService(settings_path=settings_path)

        result = service.load()

        assert result.theme == DEFAULT_THEME

    def test_returns_defaults_when_directory_not_exists(
        self, _fs, fake_home: Path
    ) -> None:
        """Loading when parent directory doesn't exist returns default settings."""
        settings_path = fake_home / ".lazyclaude" / "settings.json"
        service = SettingsService(settings_path=settings_path)

        result = service.load()

        assert result.theme == DEFAULT_THEME

    def test_loads_theme_from_valid_json(self, fs, fake_home: Path) -> None:
        """Loading from valid JSON returns correct theme."""
        settings_path = fake_home / ".lazyclaude" / "settings.json"
        fs.create_file(
            settings_path,
            contents=json.dumps({"theme": "dracula"}),
        )
        service = SettingsService(settings_path=settings_path)

        result = service.load()

        assert result.theme == "dracula"

    def test_returns_defaults_for_invalid_json(self, fs, fake_home: Path) -> None:
        """Loading from invalid JSON returns default settings."""
        settings_path = fake_home / ".lazyclaude" / "settings.json"
        fs.create_file(settings_path, contents="not valid json {{{")
        service = SettingsService(settings_path=settings_path)

        result = service.load()

        assert result.theme == DEFAULT_THEME

    def test_returns_defaults_for_missing_theme_key(self, fs, fake_home: Path) -> None:
        """Loading from JSON without theme key returns default theme."""
        settings_path = fake_home / ".lazyclaude" / "settings.json"
        fs.create_file(settings_path, contents=json.dumps({"other": "value"}))
        service = SettingsService(settings_path=settings_path)

        result = service.load()

        assert result.theme == DEFAULT_THEME


class TestSave:
    """Tests for save method."""

    def test_creates_directory_and_file(self, _fs, fake_home: Path) -> None:
        """Saving creates directory and file if they don't exist."""
        settings_path = fake_home / ".lazyclaude" / "settings.json"
        service = SettingsService(settings_path=settings_path)
        settings = AppSettings(theme="nord")

        service.save(settings)

        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["theme"] == "nord"

    def test_overwrites_existing_file(self, fs, fake_home: Path) -> None:
        """Saving overwrites existing settings file."""
        settings_path = fake_home / ".lazyclaude" / "settings.json"
        fs.create_file(settings_path, contents=json.dumps({"theme": "old"}))
        service = SettingsService(settings_path=settings_path)
        settings = AppSettings(theme="monokai")

        service.save(settings)

        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["theme"] == "monokai"


class TestRoundTrip:
    """Tests for save then load round-trip."""

    def test_round_trip_preserves_theme(self, _fs, fake_home: Path) -> None:
        """Saving and then loading returns the same theme."""
        settings_path = fake_home / ".lazyclaude" / "settings.json"
        service = SettingsService(settings_path=settings_path)
        original = AppSettings(theme="tokyo-night")

        service.save(original)
        loaded = service.load()

        assert loaded.theme == original.theme


class TestDefaultPath:
    """Tests for default settings path."""

    def test_default_path_is_lazyclaude_settings(self, _fs) -> None:
        """Service uses ~/.lazyclaude/settings.json as default path."""
        service = SettingsService()

        assert service.settings_path == Path.home() / ".lazyclaude" / "settings.json"
