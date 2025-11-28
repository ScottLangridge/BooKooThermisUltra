import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from firmware.screens.base_screen import BaseScreen
from drivers.Scale.BookooScale import BookooScale
from drivers.IODevices.IOController import IOController


class ShotProfile(BaseScreen):
    """Shot profile graphing application"""

    def __init__(self, scale: BookooScale, display: IOController):
        super().__init__(scale, display)
        # Display dimensions
        self.width = 240
        self.height = 240

        # Layout dimensions
        self.graph_height = 180  # Top section for graph
        self.info_height = 60    # Bottom section for info

        # Graph area with padding (asymmetric to accommodate labels)
        self.graph_padding_left = 27    # Extra space for Y-axis labels (weight)
        self.graph_padding_right = 30   # Space for flowrate Y-axis labels
        self.graph_padding_top = 10     # Minimal top padding
        self.graph_padding_bottom = 25  # Space for X-axis labels

        self.graph_x = self.graph_padding_left
        self.graph_y = self.graph_padding_top
        self.graph_w = self.width - self.graph_padding_left - self.graph_padding_right
        self.graph_h = self.graph_height - self.graph_padding_top - self.graph_padding_bottom

        # Fonts
        self.info_font = None
        self.axis_font = None
        self.label_font = None

        # Shot data storage
        self.shot_data = []      # List of (time, weight) tuples
        self.flowrate_data = []  # List of (time, flowrate) tuples (g/s)
        self.recording = False   # Track if we're actively recording

        # Axis scaling state
        self.x_min = 0      # X-axis minimum (time in seconds)
        self.x_max = 30     # X-axis maximum (default 30s)
        self.y_min = 0      # Y-axis minimum (weight in grams)
        self.y_max = 40     # Y-axis maximum (default 40g)
        self.flow_min = 0   # Flowrate Y-axis minimum (g/s)
        self.flow_max = 5   # Flowrate Y-axis maximum (default 5 g/s)

        # Default ranges
        self.default_x_max = 30
        self.default_y_max = 40
        self.default_flow_max = 10

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

        # Load smaller font for axis labels
        try:
            self.axis_font = ImageFont.truetype("arial.ttf", 14)
        except:
            try:
                self.axis_font = ImageFont.truetype("Arial.ttf", 14)
            except:
                self.axis_font = ImageFont.load_default()

        # Load smaller font for label labels
        try:
            self.label_font = ImageFont.truetype("arial.ttf", 12)
        except:
            try:
                self.label_font = ImageFont.truetype("Arial.ttf", 12)
            except:
                self.label_font = ImageFont.load_default()

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
                await self.scale.send_tare_and_timer_start()
                self.recording = True

        # Button B: Reset Timer
        async def on_button_b():
            await self.scale.send_timer_reset()
            self.shot_data.clear()  # Clear graph data
            self.flowrate_data.clear()  # Clear flowrate data
            # Reset scales to defaults
            self.x_max = self.default_x_max
            self.y_max = self.default_y_max
            self.flow_max = self.default_flow_max

        # LEFT Button: Return to menu
        async def on_left():
            self.stop()  # Signal to exit and return control

        # Set up button callbacks using run_coroutine_threadsafe for cross-thread async
        self.display.on_a = lambda: asyncio.run_coroutine_threadsafe(on_button_a(), loop)
        self.display.on_b = lambda: asyncio.run_coroutine_threadsafe(on_button_b(), loop)
        self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(on_left(), loop)

    def calculate_ticks(self, min_val, max_val, target_ticks=5):
        tick_step = 1
        tick_step_options = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500]
        tick_step_index = 0

        while (max_val // tick_step) > target_ticks:
            tick_step_index += 1
            tick_step = tick_step_options[tick_step_index]

        ticks = [0]
        while ticks[-1] < max_val:
            ticks.append(ticks[-1] + tick_step)

        return ticks

    def update_axis_scales(self):
        """Update axis min/max based on current state and data"""
        if not self.shot_data:
            # No data: use defaults
            self.x_min = 0
            self.x_max = self.default_x_max
            self.y_min = 0
            self.y_max = self.default_y_max
            self.flow_min = 0
            self.flow_max = self.default_flow_max
            return

        # Extract current data ranges
        times = [t for t, w in self.shot_data]
        weights = [w for t, w in self.shot_data]

        data_time_max = max(times)
        data_weight_max = max(weights)

        # Get flowrate data range
        data_flow_max = 0
        if self.flowrate_data:
            flowrates = [f for t, f in self.flowrate_data]
            if flowrates:
                data_flow_max = max(flowrates) if max(flowrates) > 0 else 0

        if self.recording:
            # DURING SHOT: Expand if needed, never shrink
            self.x_max = max(self.default_x_max, data_time_max)
            self.y_max = max(self.default_y_max, data_weight_max)
            self.flow_max = max(self.default_flow_max, data_flow_max)

            # Add small buffer to expanding axis (5% or maintain current)
            if data_time_max > self.default_x_max:
                self.x_max = data_time_max * 1.05
            if data_weight_max > self.default_y_max:
                self.y_max = data_weight_max * 1.05
            if data_flow_max > self.default_flow_max:
                self.flow_max = data_flow_max * 1.05

        else:
            # AFTER SHOT: Optimize to fit data
            # if data_time_max < self.default_x_max and data_weight_max < self.default_y_max:
                # Data fits in defaults, use fitted scale
            self.x_max = max(data_time_max * 1.1, 5)  # Min 5s display
            self.y_max = max(data_weight_max * 1.1, 10)  # Min 10g display
            self.flow_max = max(data_flow_max * 1.1, 1)  # Min 1 g/s display
            # else:
            #     # Data exceeded defaults, keep expanded view
            #     self.x_max = max(self.default_x_max, data_time_max * 1.1)
            #     self.y_max = max(self.default_y_max, data_weight_max * 1.1)

        # Always start at 0
        self.x_min = 0
        self.y_min = 0
        self.flow_min = 0

    def draw_graph_axes(self, draw):
        """Draw axes with tick marks and labels"""
        # Y-axis line
        y_start = self.graph_y
        y_end = self.graph_y + self.graph_h
        x_pos = self.graph_x
        draw.line([(x_pos, y_start), (x_pos, y_end)], fill="black", width=2)

        # X-axis line
        x_start = self.graph_x
        x_end = self.graph_x + self.graph_w
        y_pos = self.graph_y + self.graph_h
        draw.line([(x_start, y_pos), (x_end, y_pos)], fill="black", width=2)

        # Y-axis ticks and labels (grams) - use nice multiples of 5
        y_ticks = self.calculate_ticks(self.y_min, self.y_max)
        for value in y_ticks:
            # Calculate pixel position for this value
            y_norm = (value - self.y_min) / (self.y_max - self.y_min)
            pixel_y = (self.graph_y + self.graph_h) - y_norm * self.graph_h

            # Draw tick mark
            tick_length = 5
            draw.line([(x_pos - tick_length, pixel_y), (x_pos, pixel_y)],
                      fill="black", width=1)

            # Draw label (to the left of tick)
            label = f"{int(value)}"
            draw.text((x_pos - tick_length - 3, pixel_y), label,
                      fill="black", anchor="rm", font=self.axis_font)

        # X-axis ticks and labels (seconds) - use nice multiples of 5
        x_ticks = self.calculate_ticks(self.x_min, self.x_max, 10)
        for value in x_ticks:
            # Calculate pixel position for this value
            x_norm = (value - self.x_min) / (self.x_max - self.x_min)
            pixel_x = self.graph_x + x_norm * self.graph_w

            # Draw tick mark
            tick_length = 5
            draw.line([(pixel_x, y_pos), (pixel_x, y_pos + tick_length)],
                      fill="black", width=1)

            # Draw label (below tick)
            label = f"{int(value)}"
            draw.text((pixel_x, y_pos + tick_length + 2), label,
                      fill="black", anchor="mt", font=self.axis_font)

        # Right Y-axis for flowrate (g/s)
        right_x_pos = self.graph_x + self.graph_w
        draw.line([(right_x_pos, y_start), (right_x_pos, y_end)], fill="black", width=1)

        # Flowrate axis ticks and labels
        flow_ticks = self.calculate_ticks(self.flow_min, self.flow_max)
        for value in flow_ticks:
            # Calculate pixel position for this value
            flow_norm = (value - self.flow_min) / (self.flow_max - self.flow_min) if self.flow_max > 0 else 0
            pixel_y = (self.graph_y + self.graph_h) - flow_norm * self.graph_h

            # Draw tick mark
            tick_length = 5
            draw.line([(right_x_pos, pixel_y), (right_x_pos + tick_length, pixel_y)],
                      fill="black", width=1)

            # Draw label (to the right of tick)
            label = f"{int(value)}"
            draw.text((right_x_pos + tick_length + 3, pixel_y), label,
                      fill="black", anchor="lm", font=self.axis_font)

    def draw_shot_graph(self, draw):
        """Draw the weight vs time plot"""
        if len(self.shot_data) < 2:
            return  # Need at least 2 points to draw a line

        # Map data coordinates to pixel coordinates using current axis scales
        def map_to_pixels(time, weight):
            # X: time maps from x_min to x_max
            x_norm = (time - self.x_min) / (self.x_max - self.x_min)
            x = self.graph_x + x_norm * self.graph_w

            # Y: weight maps from y_min to y_max (inverted for display)
            y_norm = (weight - self.y_min) / (self.y_max - self.y_min)
            y = (self.graph_y + self.graph_h) - y_norm * self.graph_h

            return (x, y)

        # Draw lines connecting consecutive points
        for i in range(len(self.shot_data) - 1):
            p1 = map_to_pixels(*self.shot_data[i])
            p2 = map_to_pixels(*self.shot_data[i + 1])
            draw.line([p1, p2], fill="blue", width=2)

    def draw_flowrate_graph(self, draw):
        """Draw the flowrate vs time plot"""
        if len(self.flowrate_data) < 2:
            return  # Need at least 2 points to draw a line

        # Map flowrate coordinates to pixel coordinates
        def map_flowrate_to_pixels(time, flowrate):
            # X: time maps from x_min to x_max
            x_norm = (time - self.x_min) / (self.x_max - self.x_min)
            x = self.graph_x + x_norm * self.graph_w

            # Y: flowrate maps from flow_min to flow_max (inverted for display)
            flow_norm = (flowrate - self.flow_min) / (self.flow_max - self.flow_min) if self.flow_max > 0 else 0
            y = (self.graph_y + self.graph_h) - flow_norm * self.graph_h

            return (x, y)

        # Draw lines connecting consecutive points
        for i in range(len(self.flowrate_data) - 1):
            p1 = map_flowrate_to_pixels(*self.flowrate_data[i])
            p2 = map_flowrate_to_pixels(*self.flowrate_data[i + 1])
            draw.line([p1, p2], fill="red", width=2)

    def draw_info_section(self, draw):
        """Draw the bottom info section with three boxes"""
        info_y = self.graph_height
        box_width = self.width // 3

        # Draw dividing lines
        # Horizontal line separating graph from info
        draw.line([(0, info_y), (self.width, info_y)], fill="black", width=2)

        # Vertical lines dividing the three info boxes
        draw.line([(box_width, info_y), (box_width, self.height)], fill="black", width=2)
        draw.line([(box_width * 2, info_y), (box_width * 2, self.height)], fill="black", width=2)

        # Draw border around whole display
        draw.rectangle([(0, 0), (self.width-1, self.height-1)], outline="black", width=2)

        # Get real values from scale
        timer_seconds = self.scale.read_time()
        weight = self.scale.read_weight()
        current_flowrate = self.scale.read_flowrate()

        # Format values
        time_text = f"{timer_seconds:.0f}" if timer_seconds is not None else "0"
        flowrate_text = f"{current_flowrate:.1f}"
        weight_text = f"{weight:.1f}" if weight is not None else "0.0"

        # Draw numbers and labels in each box
        # Left box: Timer (seconds)
        left_center_x = box_width // 2
        value_y = info_y + (self.info_height // 2) - 6
        label_y = info_y + (self.info_height // 2) + 19
        draw.text((left_center_x, value_y), time_text, fill="black", anchor="mm", font=self.info_font)
        draw.text((left_center_x, label_y), "Time (s)", fill="black", anchor="mm", font=self.label_font)

        # Middle box: Flowrate (g/s)
        middle_center_x = box_width + (box_width // 2)
        draw.text((middle_center_x, value_y), flowrate_text, fill="black", anchor="mm", font=self.info_font)
        draw.text((middle_center_x, label_y), "Flow (g/s)", fill="black", anchor="mm", font=self.label_font)

        # Right box: Weight (grams)
        right_center_x = box_width * 2 + (box_width // 2)
        draw.text((right_center_x, value_y), weight_text, fill="black", anchor="mm", font=self.info_font)
        draw.text((right_center_x, label_y), "Weight (g)", fill="black", anchor="mm", font=self.label_font)

    async def loop(self):
        """Main loop - draw the graph layout"""
        # Collect data if recording
        if self.recording and self.scale.is_timer_running():
            current_time = self.scale.read_time()
            current_weight = self.scale.read_weight()
            current_flowrate = self.scale.read_flowrate()
            if current_time is not None and current_weight is not None:
                self.shot_data.append((current_time, current_weight))
                self.flowrate_data.append((current_time, current_flowrate))

        # Update axis scaling based on current state
        self.update_axis_scales()

        # Create display image
        img = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(img)

        # Draw graph axes
        self.draw_graph_axes(draw)

        # Draw shot data
        self.draw_shot_graph(draw)

        # Draw flowrate data
        self.draw_flowrate_graph(draw)

        # Draw info section
        self.draw_info_section(draw)

        # Update display
        self.display.draw(img)

        await asyncio.sleep(0.1)


if __name__ == "__main__":
    async def main():
        """Standalone entry point for testing"""
        from drivers.IODevices.VirtualIOController import VirtualIOController
        from firmware.screens.connection_screen import ConnectionScreen

        scale = BookooScale()
        display = VirtualIOController()

        # Connection phase
        connection_screen = ConnectionScreen(display, scale)
        await connection_screen.run_until_connected()

        # Run screen
        app = ShotProfile(scale, display)
        await app.run()

        # Cleanup
        await scale.disconnect()

    asyncio.run(main())