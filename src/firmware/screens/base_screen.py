import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from src.drivers.Scale.BookooScale import BookooScale
from src.drivers.IODevices.IOController import IOController
from src.settings import SettingsManager


class BaseScreen:
    """Abstract base class for all screens"""

    def __init__(self, scale: BookooScale, display: IOController):
        """
        Initialize screen with hardware dependencies

        Args:
            scale: Connected BookooScale instance
            display: IOController instance
        """
        self.scale = scale
        self.display = display
        self.running = False

        # Initialize settings and colorscheme
        self._settings_manager = SettingsManager.get_instance()
        self.colorscheme = self._settings_manager.get_colorscheme()

    def refresh_colorscheme(self):
        """Reload colorscheme from settings (call after settings change)"""
        self.colorscheme = self._settings_manager.get_colorscheme()

    def stop(self):
        """Signal the screen to stop and return control voluntarily"""
        self.running = False

    def show_splash(self, message, color=None):
        """
        Display a message on the screen

        Args:
            message: Text to display (supports multi-line with \\n)
            color: Text color (hex or None to use foreground from colorscheme)
        """
        if color is None:
            color = self.colorscheme.foreground

        img = Image.new("RGB", (240, 240), self.colorscheme.background)
        draw = ImageDraw.Draw(img)

        # Try to load a large font, fall back to default if not available
        font = None
        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            try:
                font = ImageFont.truetype("Arial.ttf", 30)
            except:
                font = ImageFont.load_default()

        # Split message into lines for multi-line support
        lines = message.split('\n')
        line_height = 70
        start_y = 120 - (len(lines) - 1) * line_height / 2

        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            draw.text((120, y_pos), line, fill=color, anchor="mm", font=font)

        self.display.draw(img)

    async def setup(self):
        """Override this method to add setup logic after connection"""
        pass

    async def loop(self):
        """Override this method to implement the main application loop"""
        raise NotImplementedError("Subclasses must implement loop()")

    async def run(self):
        """
        Run screen lifecycle until stop() is called.
        When this method returns, control goes back to ScreenManager.
        """
        await self.setup()
        self.running = True

        try:
            while self.running:
                await self.loop()
        except KeyboardInterrupt:
            # Stop the screen gracefully, then re-raise to trigger cleanup
            self.running = False
            raise

        # When running becomes False, loop exits and control returns