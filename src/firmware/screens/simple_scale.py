import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from src.firmware.screens.interactive_screen import InteractiveScreen
from src.drivers.Scale.BookooScale import BookooScale
from src.drivers.IODevices.IOController import IOController


class SimpleScale(InteractiveScreen):
    """Simple scale display with timer and tare controls"""

    def __init__(self, scale: BookooScale, display: IOController):
        super().__init__(scale, display)
        self.weight_font = None
        self.hint_font = None
        self.timer_running = False

    async def setup(self):
        """Initialize fonts and button callbacks"""
        # Load fonts using inherited load_font() method
        self.weight_font = self.load_font("arial", 80)
        self.hint_font = self.load_font("arial", 16)

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

        # LEFT Button: Return to menu
        async def on_left():
            self.stop()  # Signal to exit and return control

        # Set up button callbacks using inherited bind_button() helper
        self.bind_button('a', on_button_a)
        self.bind_button('b', on_button_b)
        self.bind_button('left', on_left)

    async def loop(self):
        """Main display loop"""
        # Get current weight
        weight = self.scale.read_weight()

        # Create display image
        img = Image.new("RGB", (self.display.width, self.display.height), "white")
        draw = ImageDraw.Draw(img)

        # Draw weight in center with large font
        center_x = self.display.width // 2
        center_y = self.display.height // 2
        if weight is not None:
            weight_text = f"{weight:.1f}g"
            draw.text((center_x, center_y), weight_text, fill="black", anchor="mm", font=self.weight_font)
        else:
            draw.text((center_x, center_y), "No reading", fill="red", anchor="mm", font=self.weight_font)

        # Draw button hints at bottom
        timer_status = "running" if self.timer_running else "stopped"
        hint_text = f"A: Timer ({timer_status})  |  B: Tare"
        draw.text((center_x, self.display.height - 20), hint_text, fill="gray", anchor="mm", font=self.hint_font)

        # Update display
        self.display.draw(img)


if __name__ == "__main__":
    async def main():
        """Standalone entry point for testing"""
        from src.drivers.IODevices.VirtualIOController import VirtualIOController
        from src.firmware.screens.connection_screen import ConnectionScreen

        scale = BookooScale()
        display = VirtualIOController()

        # Connection phase
        connection_screen = ConnectionScreen(display, scale)
        await connection_screen.run_until_connected()

        # Run screen
        app = SimpleScale(scale, display)
        await app.run()

        # Cleanup
        await scale.disconnect()

    asyncio.run(main())