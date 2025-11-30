import sys
from pathlib import Path
from abc import ABC

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from src.drivers.IODevices.IOController import IOController


class Screen(ABC):
    """
    Abstract base class for all screen types

    Provides common properties and utilities that all screens need,
    including display controller and helper methods for rendering.
    """

    def __init__(self, display: IOController):
        """
        Initialize screen with display controller

        Args:
            display: IOController instance for rendering to hardware
        """
        self.display = display
        self.width = 240
        self.height = 240

        # Future: Colorscheme support
        # self.colorscheme = ColorScheme()

    def show_splash(self, message: str, color: str = "black"):
        """
        Display a centered message on the screen

        Creates a white background with centered text. Supports
        multi-line messages using newline characters.

        Args:
            message: Text to display (use '\n' for multiple lines)
            color: Text color (default: "black")

        Example:
            screen.show_splash("Connecting...")
            screen.show_splash("Connection\nFailed", "red")
        """
        img = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(img)

        font = self.load_font(size=30)

        # Split message into lines for multi-line support
        lines = message.split('\n')
        line_height = 70
        start_y = 120 - (len(lines) - 1) * line_height / 2

        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            draw.text(
                (120, y_pos),
                line,
                fill=color,
                anchor="mm",
                font=font
            )

        self.display.draw(img)

    def load_font(self, font_name: str = "arial", size: int = 30):
        """
        Load a TrueType font with automatic fallback

        Tries to load the font in lowercase, then capitalized, then
        falls back to the default PIL font if neither is found.

        Args:
            font_name: Font name without extension (default: "arial")
            size: Font size in points (default: 30)

        Returns:
            ImageFont instance (TrueType or default)

        Example:
            font = screen.load_font("arial", 20)
            large_font = screen.load_font("arial", 80)
        """
        try:
            return ImageFont.truetype(f"{font_name.lower()}.ttf", size)
        except:
            try:
                return ImageFont.truetype(f"{font_name.capitalize()}.ttf", size)
            except:
                return ImageFont.load_default()
