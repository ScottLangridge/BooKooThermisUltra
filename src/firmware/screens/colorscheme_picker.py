import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from src.firmware.screens.base_screen import BaseScreen
from src.drivers.Scale.BookooScale import BookooScale
from src.drivers.IODevices.IOController import IOController


class ColorschemePickerScreen(BaseScreen):
    """Colorscheme selection screen with live preview"""

    def __init__(self, scale: BookooScale, display: IOController):
        super().__init__(scale, display)

        # Display dimensions
        self.width = 240
        self.height = 240

        # Layout
        self.header_height = 40
        self.preview_height = 120
        self.list_height = 80

        # Available colorschemes
        self.available_colorschemes = self._settings_manager.get_available_colorschemes()
        self.current_index = 0
        self.original_colorscheme_name = self._settings_manager.get('colorscheme')

        # Find current colorscheme index
        try:
            self.current_index = self.available_colorschemes.index(self.original_colorscheme_name)
        except ValueError:
            self.current_index = 0

        # Fonts
        self.header_font = None
        self.list_font = None

    async def setup(self):
        """Initialize fonts and button callbacks"""
        print("Starting colorscheme picker...")

        # Load fonts
        try:
            self.header_font = ImageFont.truetype("arial.ttf", 24)
        except:
            try:
                self.header_font = ImageFont.truetype("Arial.ttf", 24)
            except:
                self.header_font = ImageFont.load_default()

        try:
            self.list_font = ImageFont.truetype("arial.ttf", 18)
        except:
            try:
                self.list_font = ImageFont.truetype("Arial.ttf", 18)
            except:
                self.list_font = ImageFont.load_default()

        # Get reference to the main event loop for cross-thread async calls
        loop = asyncio.get_event_loop()

        # Button handlers
        async def on_up():
            self.current_index = (self.current_index - 1) % len(self.available_colorschemes)
            self.update_colorscheme()

        async def on_down():
            self.current_index = (self.current_index + 1) % len(self.available_colorschemes)
            self.update_colorscheme()

        async def on_left():
            # Save and exit
            self._settings_manager.save()
            print(f"Saved colorscheme: {self._settings_manager.get('colorscheme')}")
            self.stop()

        # Set up button callbacks
        self.display.on_up = lambda: asyncio.run_coroutine_threadsafe(on_up(), loop)
        self.display.on_down = lambda: asyncio.run_coroutine_threadsafe(on_down(), loop)
        self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(on_left(), loop)

    def update_colorscheme(self):
        """Update current colorscheme selection (in-memory, saved on exit)"""
        selected_name = self.available_colorschemes[self.current_index]
        self._settings_manager.set('colorscheme', selected_name)
        self.refresh_colorscheme()

    def draw_header(self, draw):
        """Draw title"""
        draw.text(
            (self.width // 2, self.header_height // 2),
            "CHOOSE COLOURSCHEME",
            fill=self.colorscheme.foreground,
            anchor="mm",
            font=self.header_font
        )

    def draw_preview(self, draw):
        """Draw preview graph showing colorscheme"""
        # Preview area bounds
        preview_y = self.header_height
        preview_w = 200
        preview_h = 100
        preview_x = (self.width - preview_w) // 2
        preview_y_offset = preview_y + 10

        # Graph area (smaller version of shot profile)
        graph_padding = 20
        graph_x = preview_x + graph_padding
        graph_y = preview_y_offset
        graph_w = preview_w - 2 * graph_padding
        graph_h = preview_h

        # Draw axes
        # Y-axis
        draw.line(
            [(graph_x, graph_y), (graph_x, graph_y + graph_h)],
            fill=self.colorscheme.foreground,
            width=2
        )
        # X-axis
        draw.line(
            [(graph_x, graph_y + graph_h), (graph_x + graph_w, graph_y + graph_h)],
            fill=self.colorscheme.foreground,
            width=2
        )

        # Draw sample data lines (fake shot profile)
        # Weight line (secondary_accent)
        weight_points = [
            (0, 100), (20, 90), (40, 70), (60, 50), (80, 30), (100, 10)
        ]
        for i in range(len(weight_points) - 1):
            x1_norm, y1_norm = weight_points[i]
            x2_norm, y2_norm = weight_points[i + 1]

            x1 = graph_x + (x1_norm / 100) * graph_w
            y1 = graph_y + (y1_norm / 100) * graph_h
            x2 = graph_x + (x2_norm / 100) * graph_w
            y2 = graph_y + (y2_norm / 100) * graph_h

            draw.line([(x1, y1), (x2, y2)], fill=self.colorscheme.secondary_accent, width=2)

        # Flowrate line (tertiary_accent)
        flow_points = [
            (0, 90), (20, 50), (40, 30), (60, 40), (80, 70), (100, 95)
        ]
        for i in range(len(flow_points) - 1):
            x1_norm, y1_norm = flow_points[i]
            x2_norm, y2_norm = flow_points[i + 1]

            x1 = graph_x + (x1_norm / 100) * graph_w
            y1 = graph_y + (y1_norm / 100) * graph_h
            x2 = graph_x + (x2_norm / 100) * graph_w
            y2 = graph_y + (y2_norm / 100) * graph_h

            draw.line([(x1, y1), (x2, y2)], fill=self.colorscheme.tertiary_accent, width=2)

    def draw_list(self, draw):
        """Draw colorscheme list"""
        list_y = self.header_height + self.preview_height
        row_height = 26

        # Show 3 items: one above, current (highlighted), one below
        visible_count = 3
        start_index = max(0, self.current_index - 1)

        for i in range(visible_count):
            idx = start_index + i
            if idx >= len(self.available_colorschemes):
                break

            colorscheme_name = self.available_colorschemes[idx]
            is_current = (idx == self.current_index)

            y_pos = list_y + i * row_height

            # Draw background for highlighted item
            if is_current:
                draw.rectangle(
                    [(0, y_pos), (self.width, y_pos + row_height)],
                    fill=self.colorscheme.primary_accent
                )
                text_color = self.colorscheme.background
            else:
                text_color = self.colorscheme.foreground

            # Draw colorscheme name
            draw.text(
                (self.width // 2, y_pos + row_height // 2),
                colorscheme_name,
                fill=text_color,
                anchor="mm",
                font=self.list_font
            )

    async def loop(self):
        """Main render loop"""
        # Create display image
        img = Image.new("RGB", (self.width, self.height), self.colorscheme.background)
        draw = ImageDraw.Draw(img)

        # Draw all sections
        self.draw_header(draw)
        self.draw_preview(draw)
        self.draw_list(draw)

        # Update display
        self.display.draw(img)

        # Refresh at 20Hz
        await asyncio.sleep(0.05)
