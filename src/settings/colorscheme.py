"""ColorScheme class for managing color themes"""

import json
from pathlib import Path
from typing import Dict


class ColorScheme:
    """Represents a color scheme with named color slots"""

    def __init__(self, name: str, colors: dict):
        """
        Initialize a colorscheme from color data

        Args:
            name: Name of the colorscheme (e.g., "Dark", "Light")
            colors: Dictionary containing color values for each slot
        """
        self.name = name

        # Required color slots
        self.background = colors.get('background', '#ffffff')
        self.foreground = colors.get('foreground', '#000000')
        self.primary_accent = colors.get('primary_accent', '#0066cc')
        self.secondary_accent = colors.get('secondary_accent', '#0099cc')
        self.tertiary_accent = colors.get('tertiary_accent', '#cc6600')
        self.success = colors.get('success', '#00aa00')
        self.error = colors.get('error', '#cc0000')
        self.info = colors.get('info', '#0066cc')

    @staticmethod
    def _get_colorschemes_path() -> Path:
        """Get path to colorschemes.json file"""
        # Assume we're in src/settings/, go up to project root
        return Path(__file__).parent.parent.parent / 'config' / 'colorschemes.json'

    @staticmethod
    def load_all() -> Dict[str, 'ColorScheme']:
        """
        Load all available colorschemes from colorschemes.json

        Returns:
            Dictionary mapping colorscheme names to ColorScheme objects
        """
        colorschemes_path = ColorScheme._get_colorschemes_path()

        if not colorschemes_path.exists():
            # Create default colorschemes file if it doesn't exist
            ColorScheme._create_default_colorschemes_file(colorschemes_path)

        try:
            with open(colorschemes_path, 'r') as f:
                data = json.load(f)

            colorschemes = {}
            for name, colors in data.items():
                colorschemes[name] = ColorScheme(name, colors)

            return colorschemes

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading colorschemes.json: {e}")
            # Return a minimal default colorscheme
            return {
                'Dark': ColorScheme('Dark', {
                    'background': '#1e1e1e',
                    'foreground': '#d4d4d4',
                    'primary_accent': '#0e639c',
                    'secondary_accent': '#4ec9b0',
                    'tertiary_accent': '#ce9178',
                    'success': '#4ec9b0',
                    'error': '#f48771',
                    'info': '#569cd6'
                })
            }

    @staticmethod
    def load(name: str) -> 'ColorScheme':
        """
        Load a specific colorscheme by name

        Args:
            name: Name of the colorscheme to load

        Returns:
            ColorScheme object, or default Dark theme if not found
        """
        all_colorschemes = ColorScheme.load_all()

        if name in all_colorschemes:
            return all_colorschemes[name]
        else:
            print(f"Warning: Colorscheme '{name}' not found, using Dark")
            return all_colorschemes.get('Dark', ColorScheme('Dark', {}))

    @staticmethod
    def _create_default_colorschemes_file(path: Path):
        """Create default colorschemes.json file"""
        path.parent.mkdir(parents=True, exist_ok=True)

        default_colorschemes = {
            "Dark": {
                "background": "#1e1e1e",
                "foreground": "#d4d4d4",
                "primary_accent": "#0e639c",
                "secondary_accent": "#4ec9b0",
                "tertiary_accent": "#ce9178",
                "success": "#4ec9b0",
                "error": "#f48771",
                "info": "#569cd6"
            },
            "Light": {
                "background": "#ffffff",
                "foreground": "#000000",
                "primary_accent": "#0066cc",
                "secondary_accent": "#0099cc",
                "tertiary_accent": "#cc6600",
                "success": "#00aa00",
                "error": "#cc0000",
                "info": "#0066cc"
            }
        }

        with open(path, 'w') as f:
            json.dump(default_colorschemes, f, indent=2)

        print(f"Created default colorschemes file at {path}")

    def __repr__(self):
        return f"ColorScheme(name='{self.name}')"
