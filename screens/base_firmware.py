import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from drivers.Scale.BookooScale import BookooScale
from drivers.IODevices.VirtualIOController import VirtualIOController


class BaseFirmware:
    """Base class for screens applications with scale and display"""

    def __init__(self):
        self.scale = None
        self.display = None

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

    async def connect_to_scale(self):
        """Connect to scale with infinite retry"""
        connected = False
        while not connected:
            self.show_splash("Connecting...", "blue")
            print("Connecting to scale...")
            connected = await self.scale.establish_connection()

            if not connected:
                print("Failed to connect to scale, retrying...")
                self.show_splash("Connection\nFailed", "red")
                await asyncio.sleep(1)

        print("Connected!")

    async def setup(self):
        """Override this method to add setup logic after connection"""
        pass

    async def loop(self):
        """Override this method to implement the main application loop"""
        raise NotImplementedError("Subclasses must implement loop()")

    async def run(self):
        """Main entry point - handles initialization and cleanup"""
        # Initialize hardware
        self.scale = BookooScale()
        self.display = VirtualIOController()

        # Connect to scale
        await self.connect_to_scale()

        # Run subclass setup
        await self.setup()

        try:
            # Run the main loop
            while True:
                await self.loop()

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await self.scale.disconnect()