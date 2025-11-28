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

        # Shot data storage
        self.shot_data = []      # List of (time, weight) tuples
        self.recording = False   # Track if we're actively recording

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
                # Stop recording
                await self.scale.send_timer_stop()
                self.recording = False
            else:
                # Start recording
                await self.scale.send_timer_start()
                self.recording = True

        # Button B: Reset Timer
        async def on_button_b():
            await self.scale.send_timer_reset()
            self.shot_data.clear()  # Clear graph data

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

    def draw_shot_graph(self, draw):
        """Draw the weight vs time plot"""
        if len(self.shot_data) < 2:
            return  # Need at least 2 points to draw a line

        # Find data ranges for scaling
        times = [t for t, w in self.shot_data]
        weights = [w for t, w in self.shot_data]

        time_min = min(times)
        time_max = max(times)
        weight_min = min(weights)
        weight_max = max(weights)

        # Add padding to ranges (avoid divide by zero)
        time_range = max(time_max - time_min, 1)
        weight_range = max(weight_max - weight_min, 1)

        # Map data coordinates to pixel coordinates
        def map_to_pixels(time, weight):
            # X: time maps to graph_x to graph_x + graph_w
            x = self.graph_x + ((time - time_min) / time_range) * self.graph_w

            # Y: weight maps to graph_y + graph_h (bottom) to graph_y (top)
            # Note: y coordinates are inverted (0 is top)
            y = (self.graph_y + self.graph_h) - ((weight - weight_min) / weight_range) * self.graph_h

            return (x, y)

        # Draw lines connecting consecutive points
        for i in range(len(self.shot_data) - 1):
            p1 = map_to_pixels(*self.shot_data[i])
            p2 = map_to_pixels(*self.shot_data[i + 1])
            draw.line([p1, p2], fill="blue", width=2)

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
        # Collect data if recording
        if self.recording and self.scale.is_timer_running():
            current_time = self.scale.read_time()
            current_weight = self.scale.read_weight()
            if current_time is not None and current_weight is not None:
                self.shot_data.append((current_time, current_weight))

        # Create display image
        img = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(img)

        # Draw graph axes
        self.draw_graph_axes(draw)

        # Draw shot data
        self.draw_shot_graph(draw)

        # Draw info section
        self.draw_info_section(draw)

        # Update display
        self.display.draw(img)

        await asyncio.sleep(0.1)


if __name__ == "__main__":
    app = ShotProfile()
    asyncio.run(app.run())