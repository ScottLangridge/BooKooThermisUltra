import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from drivers.Scale.BookooScale import BookooScale
from drivers.IODevices.IOController import IOController


class ConnectionScreen:
    """Dedicated screen for scale connection with visual feedback"""

    def __init__(self, display: IOController, scale: BookooScale):
        """
        Initialize connection screen

        Args:
            display: IOController instance for visual feedback
            scale: BookooScale instance (not yet connected)
        """
        self.display = display
        self.scale = scale

    def show_splash(self, message, color="black"):
        """Display connection status message"""
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

    async def attempt_connection(self) -> bool:
        """
        Single connection attempt with visual feedback

        Returns:
            True if connection succeeded, False otherwise
        """
        self.show_splash("Connecting...", "blue")
        print("Connecting to scale...")

        connected = await self.scale.establish_connection()

        if not connected:
            print("Failed to connect to scale")
            self.show_splash("Connection\nFailed", "red")
            await asyncio.sleep(1)
        else:
            print("Connected!")
            self.show_splash("Connected!", "green")
            await asyncio.sleep(0.5)

        return connected

    async def run_until_connected(self):
        """
        Connect with infinite retry (non-blocking for transitions)

        This method blocks until connection succeeds, providing visual feedback
        for each attempt. When it returns, the scale is connected and ready.
        """
        while True:
            if await self.attempt_connection():
                return  # Success - caller can transition to next screen
