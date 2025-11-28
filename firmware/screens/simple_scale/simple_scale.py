import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from firmware.screens.base_screen import BaseScreen


class SimpleScale(BaseScreen):
    """Simple scale display with timer and tare controls"""

    def __init__(self):
        super().__init__()
        self.weight_font = None
        self.hint_font = None
        self.timer_running = False

    async def setup(self):
        """Initialize fonts and button callbacks"""
        print("Starting display loop...")

        # Load fonts for display
        try:
            self.weight_font = ImageFont.truetype("arial.ttf", 80)
            self.hint_font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                self.weight_font = ImageFont.truetype("Arial.ttf", 80)
                self.hint_font = ImageFont.truetype("Arial.ttf", 16)
            except:
                self.weight_font = ImageFont.load_default()
                self.hint_font = ImageFont.load_default()

        # Get reference to the main event loop for cross-thread async calls
        loop = asyncio.get_event_loop()

        # Button A: Start/Stop Timer
        async def on_button_a():
            if self.timer_running:
                await self.scale.send_timer_stop()
                self.timer_running = False
                print("Timer stopped")
            else:
                await self.scale.send_timer_start()
                self.timer_running = True
                print("Timer started")

        # Button B: Tare
        async def on_button_b():
            await self.scale.send_tare()
            print("Tared")

        # Set up button callbacks using run_coroutine_threadsafe for cross-thread async
        self.display.on_a = lambda: asyncio.run_coroutine_threadsafe(on_button_a(), loop)
        self.display.on_b = lambda: asyncio.run_coroutine_threadsafe(on_button_b(), loop)

    async def loop(self):
        """Main display loop - runs at 10Hz"""
        # Get current weight
        weight = self.scale.read_weight()

        # Create display image
        img = Image.new("RGB", (240, 240), "white")
        draw = ImageDraw.Draw(img)

        # Draw weight in center with large font
        if weight is not None:
            weight_text = f"{weight:.1f}g"
            draw.text((120, 120), weight_text, fill="black", anchor="mm", font=self.weight_font)
        else:
            draw.text((120, 120), "No reading", fill="red", anchor="mm", font=self.weight_font)

        # Draw button hints at bottom
        timer_status = "running" if self.timer_running else "stopped"
        hint_text = f"A: Timer ({timer_status})  |  B: Tare"
        draw.text((120, 220), hint_text, fill="gray", anchor="mm", font=self.hint_font)

        # Update display
        self.display.draw(img)

        # Update at 10Hz
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    app = SimpleScale()
    asyncio.run(app.run())