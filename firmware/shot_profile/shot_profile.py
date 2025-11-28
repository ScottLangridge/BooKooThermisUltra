import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from base_firmware import BaseFirmware


class ShotProfile(BaseFirmware):
    """Shot profile graphing application"""

    def __init__(self):
        super().__init__()
        # Display dimensions
        self.width = 240
        self.height = 240

        # Layout dimensions
        self.graph_height = 180  # Top section for graph
        self.info_height = 60    # Bottom section for info

        # Graph area with padding
        self.graph_padding = 20
        self.graph_x = self.graph_padding
        self.graph_y = self.graph_padding
        self.graph_w = self.width - (2 * self.graph_padding)
        self.graph_h = self.graph_height - (2 * self.graph_padding)

        # Fonts
        self.info_font = None

    async def setup(self):
        """Initialize after connection"""
        print("Starting shot profile...")

        # Load font for info display
        try:
            self.info_font = ImageFont.truetype("arial.ttf", 32)
        except:
            try:
                self.info_font = ImageFont.truetype("Arial.ttf", 32)
            except:
                self.info_font = ImageFont.load_default()

        # Get reference to the main event loop for cross-thread async calls
        loop = asyncio.get_event_loop()

        # Button A: Start/Stop Timer
        async def on_button_a():
            if self.scale.is_timer_running():
                await self.scale.send_timer_stop()
            else:
                await self.scale.send_timer_start()

        # Button B: Reset Timer
        async def on_button_b():
            await self.scale.send_timer_reset()

        # Set up button callbacks using run_coroutine_threadsafe for cross-thread async
        self.display.on_a = lambda: asyncio.run_coroutine_threadsafe(on_button_a(), loop)
        self.display.on_b = lambda: asyncio.run_coroutine_threadsafe(on_button_b(), loop)

    def draw_graph_axes(self, draw):
        """Draw the axes for the graph"""
        # Y-axis (vertical line on left)
        y_start = self.graph_y
        y_end = self.graph_y + self.graph_h
        x_pos = self.graph_x
        draw.line([(x_pos, y_start), (x_pos, y_end)], fill="black", width=2)

        # X-axis (horizontal line on bottom)
        x_start = self.graph_x
        x_end = self.graph_x + self.graph_w
        y_pos = self.graph_y + self.graph_h
        draw.line([(x_start, y_pos), (x_end, y_pos)], fill="black", width=2)

    def draw_info_section(self, draw):
        """Draw the bottom info section with two boxes"""
        info_y = self.graph_height
        box_width = self.width // 2

        # Draw dividing lines
        # Horizontal line separating graph from info
        draw.line([(0, info_y), (self.width, info_y)], fill="black", width=2)

        # Vertical line dividing the two info boxes
        draw.line([(box_width, info_y), (box_width, self.height)], fill="black", width=2)

        # Draw border around whole display
        draw.rectangle([(0, 0), (self.width-1, self.height-1)], outline="black", width=2)

        # Get real values from scale
        timer_seconds = self.scale.read_time()
        weight = self.scale.read_weight()

        # Format values
        time_text = f"{timer_seconds:.0f}" if timer_seconds is not None else "0"
        weight_text = f"{weight:.1f}" if weight is not None else "0.0"

        # Draw numbers in each box
        # Left box: Timer (seconds)
        left_center_x = box_width // 2
        left_center_y = info_y + (self.info_height // 2)
        draw.text((left_center_x, left_center_y), time_text, fill="black", anchor="mm", font=self.info_font)

        # Right box: Weight (grams)
        right_center_x = box_width + (box_width // 2)
        right_center_y = info_y + (self.info_height // 2)
        draw.text((right_center_x, right_center_y), weight_text, fill="black", anchor="mm", font=self.info_font)

    async def loop(self):
        """Main loop - draw the graph layout"""
        # Create display image
        img = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(img)

        # Draw graph axes
        self.draw_graph_axes(draw)

        # Draw info section
        self.draw_info_section(draw)

        # Update display
        self.display.draw(img)

        await asyncio.sleep(0.1)


if __name__ == "__main__":
    app = ShotProfile()
    asyncio.run(app.run())