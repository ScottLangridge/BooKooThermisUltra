"""SettingsManager class for managing application settings"""

import json
from pathlib import Path
from typing import Any, List
from .colorscheme import ColorScheme


class SettingsManager:
    """Manages application settings with default and user overrides"""

    _instance = None  # Singleton instance

    @classmethod
    def get_instance(cls) -> 'SettingsManager':
        """
        Get the singleton instance of SettingsManager

        Returns:
            The singleton SettingsManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize settings manager (load defaults and user settings)"""
        if SettingsManager._instance is not None:
            raise RuntimeError("SettingsManager is a singleton. Use get_instance() instead.")

        self._config_dir = Path(__file__).parent.parent.parent / 'config'
        self._default_settings_path = self._config_dir / 'default_settings.json'
        self._settings_path = self._config_dir / 'settings.json'

        # Load settings
        self._defaults = self._load_defaults()
        self._user_settings = self._load_user_settings()

        # Merged settings (defaults + user overrides)
        self._settings = {**self._defaults, **self._user_settings}

        # Cache colorschemes
        self._colorschemes = ColorScheme.load_all()

    def _load_defaults(self) -> dict:
        """Load default settings from default_settings.json"""
        if not self._default_settings_path.exists():
            # Create default settings file
            self._create_default_settings_file()

        try:
            with open(self._default_settings_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading default_settings.json: {e}")
            return {'colorscheme': 'Dark'}

    def _load_user_settings(self) -> dict:
        """Load user settings from settings.json"""
        if not self._settings_path.exists():
            # Create empty user settings file
            self._create_empty_user_settings_file()
            return {}

        try:
            with open(self._settings_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading settings.json: {e}")
            # Rename corrupted file and create fresh one
            backup_path = self._settings_path.with_suffix('.json.backup')
            try:
                self._settings_path.rename(backup_path)
                print(f"Renamed corrupted settings.json to {backup_path.name}")
            except:
                pass
            self._create_empty_user_settings_file()
            return {}

    def _create_default_settings_file(self):
        """Create default_settings.json with default values"""
        self._config_dir.mkdir(parents=True, exist_ok=True)

        defaults = {
            'colorscheme': 'Dark'
        }

        with open(self._default_settings_path, 'w') as f:
            json.dump(defaults, f, indent=2)

        print(f"Created default settings file at {self._default_settings_path}")

    def _create_empty_user_settings_file(self):
        """Create empty settings.json file"""
        self._config_dir.mkdir(parents=True, exist_ok=True)

        with open(self._settings_path, 'w') as f:
            json.dump({}, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value (user override if exists, otherwise default setting)
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set a setting value (in-memory, call save() to persist)

        Args:
            key: Setting key
            value: Setting value
        """
        self._settings[key] = value
        self._user_settings[key] = value

    def save(self):
        """Save user settings to settings.json"""
        try:
            with open(self._settings_path, 'w') as f:
                json.dump(self._user_settings, f, indent=2)
            print(f"Settings saved to {self._settings_path}")
        except IOError as e:
            print(f"Error saving settings: {e}")

    def get_colorscheme(self) -> ColorScheme:
        """
        Get the current colorscheme object

        Returns:
            ColorScheme object for the current colorscheme setting
        """
        colorscheme_name = self.get('colorscheme', 'Dark')

        if colorscheme_name in self._colorschemes:
            return self._colorschemes[colorscheme_name]
        else:
            print(f"Warning: Colorscheme '{colorscheme_name}' not found, using Dark")
            return self._colorschemes.get('Dark', ColorScheme('Dark', {}))

    def get_available_colorschemes(self) -> List[str]:
        """
        Get list of available colorscheme names

        Returns:
            List of colorscheme names
        """
        return list(self._colorschemes.keys())

    def reload_colorschemes(self):
        """Reload colorschemes from disk (useful if colorschemes.json changes)"""
        self._colorschemes = ColorScheme.load_all()
