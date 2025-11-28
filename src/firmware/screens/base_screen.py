import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from src.drivers.Scale.BookooScale import BookooScale
from src.drivers.IODevices.IOController import IOController


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

    def stop(self):
        """Signal the screen to stop and return control voluntarily"""
        self.running = False

    def show_splash(self, message, color="black"):
        """Display a message on the screen"""
        img = Image.new("RGB", (240, 240), "white")
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
            print("\nShutting down...")

        # When running becomes False, loop exits and control returns