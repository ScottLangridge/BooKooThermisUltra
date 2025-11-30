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

        # Future: Colorscheme support
        # self.colorscheme = ColorScheme()

    def create_canvas(self, background: str = "white") -> Image.Image:
        """
        Create a new blank canvas image for the display

        Common helper to create PIL Image instances with correct dimensions.
        Simplifies the pattern: Image.new("RGB", (width, height), color)

        Args:
            background: Background color (default: "white")

        Returns:
            PIL Image instance sized for this display

        Example:
            img = self.create_canvas()
            img = self.create_canvas(background="black")
        """
        return Image.new("RGB", (self.display.width, self.display.height), background)

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
        img = self.create_canvas()
        draw = ImageDraw.Draw(img)

        font = self.load_font(size=30)

        # Split message into lines for multi-line support
        lines = message.split('\n')
        line_height = 70
        start_y = (self.display.height // 2) - (len(lines) - 1) * line_height / 2

        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            draw.text(
                (self.display.width // 2, y_pos),
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
