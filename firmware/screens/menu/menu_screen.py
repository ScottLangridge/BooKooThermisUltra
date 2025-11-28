import asyncio
import sys
from pathlib import Path
from math import ceil

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from firmware.screens.base_screen import BaseScreen
from firmware.screens.menu.menu_option import MenuOption
from drivers.Scale.BookooScale import BookooScale
from drivers.IODevices.IOController import IOController


class MenuScreen(BaseScreen):
    """Main menu firmware that handles rendering and navigation"""

    def __init__(self, scale: BookooScale, display: IOController,
                 title: str, options: list[MenuOption], items_per_page: int = 5,
                 header_height: int = 40, footer_height: int = 40):
        """
        Create a menu screen

        Args:
            scale: Connected BookooScale instance
            display: IOController instance
            title: Menu title displayed in header
            options: List of all menu options
            items_per_page: Number of options visible at once (default: 5)
            header_height: Fixed height for title section (default: 40)
            footer_height: Fixed height for page indicator (default: 40)
        """
        super().__init__(scale, display)

        # Configuration
        self.title = title
        self.options = options
        self.items_per_page = items_per_page
        self.header_height = header_height
        self.footer_height = footer_height

        # Display dimensions
        self.width = 240
        self.height = 240

        # State
        self.current_index = 0
        self.current_page = 0
        self.total_pages = ceil(len(options) / items_per_page) if options else 1

        # Fonts (will be initialized in setup)
        self.title_font = None
        self.option_font = None
        self.footer_font = None

        # Layout (calculated)
        self.menu_area_height = 0
        self.row_height = 0

        # Calculate initial layout
        self.calculate_layout()

    def calculate_layout(self):
        """Compute row heights and prepare for font sizing"""
        # Available space for menu items
        self.menu_area_height = self.height - self.header_height - self.footer_height

        # Fixed row height based on items_per_page
        self.row_height = self.menu_area_height // self.items_per_page

    def move_up(self):
        """Move highlight up, handle paging"""
        if self.current_index > 0:
            self.current_index -= 1
            # Page automatically updates based on current_index
            self.current_page = self.current_index // self.items_per_page

    def move_down(self):
        """Move highlight down, handle paging"""
        if self.current_index < len(self.options) - 1:
            self.current_index += 1
            # Scrolling past last visible item automatically pages
            self.current_page = self.current_index // self.items_per_page

    def get_visible_options(self):
        """Returns list of options for current page"""
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.options[start_idx:end_idx]

    def draw_header(self, draw):
        """Render title section"""
        # Fill header background (white)
        draw.rectangle([(0, 0), (self.width, self.header_height)], fill="white")

        # Draw title text (centered)
        draw.text(
            (self.width // 2, self.header_height // 2),
            self.title,
            fill="black",
            anchor="mm",
            font=self.title_font
        )

        # Draw bottom border
        draw.line(
            [(0, self.header_height), (self.width, self.header_height)],
            fill="black",
            width=2
        )

    def draw_footer(self, draw):
        """Render page indicator"""
        footer_y = self.height - self.footer_height

        # Draw top border
        draw.line(
            [(0, footer_y), (self.width, footer_y)],
            fill="black",
            width=2
        )

        # Draw page indicator (centered)
        page_text = f"page {self.current_page + 1}/{self.total_pages}"
        draw.text(
            (self.width // 2, footer_y + self.footer_height // 2),
            page_text,
            fill="black",
            anchor="mm",
            font=self.footer_font
        )

    def draw_option_row(self, draw, option: MenuOption, y_position: int, is_highlighted: bool):
        """Render single menu item"""
        # Determine colors
        bg_color = "black" if is_highlighted else "white"
        text_color = "white" if is_highlighted else "black"

        # Draw background
        draw.rectangle(
            [(0, y_position), (self.width, y_position + self.row_height)],
            fill=bg_color
        )

        # Draw option text (left-aligned with padding)
        draw.text(
            (10, y_position + self.row_height // 2),
            option.label,
            fill=text_color,
            anchor="lm",
            font=self.option_font
        )

        # Draw icon (right-aligned with padding)
        draw.text(
            (self.width - 10, y_position + self.row_height // 2),
            option.icon,
            fill=text_color,
            anchor="rm",
            font=self.option_font
        )

        # Draw border between items
        draw.line(
            [(0, y_position + self.row_height), (self.width, y_position + self.row_height)],
            fill="black",
            width=2
        )

    def draw_menu_items(self, draw):
        """Render visible menu options"""
        if not self.options:
            # Handle empty options list
            y_center = self.header_height + self.menu_area_height // 2
            draw.text(
                (self.width // 2, y_center),
                "No options available",
                fill="black",
                anchor="mm",
                font=self.option_font
            )
            return

        visible_options = self.get_visible_options()
        start_idx = self.current_page * self.items_per_page

        for i, option in enumerate(visible_options):
            option_idx = start_idx + i
            y_position = self.header_height + i * self.row_height
            is_highlighted = (option_idx == self.current_index)
            self.draw_option_row(draw, option, y_position, is_highlighted)

    async def setup(self):
        """Configure button handlers for up/down navigation"""
        print("Starting menu...")

        # Load fonts with fallbacks
        # Title font (based on header height)
        title_size = int(self.header_height * 0.6)
        try:
            self.title_font = ImageFont.truetype("arial.ttf", title_size)
        except:
            try:
                self.title_font = ImageFont.truetype("Arial.ttf", title_size)
            except:
                self.title_font = ImageFont.load_default()

        # Option font (based on row height)
        option_size = int(self.row_height * 0.6)
        try:
            self.option_font = ImageFont.truetype("arial.ttf", option_size)
        except:
            try:
                self.option_font = ImageFont.truetype("Arial.ttf", option_size)
            except:
                self.option_font = ImageFont.load_default()

        # Footer font (based on footer height)
        footer_size = int(self.footer_height * 0.4)
        try:
            self.footer_font = ImageFont.truetype("arial.ttf", footer_size)
        except:
            try:
                self.footer_font = ImageFont.truetype("Arial.ttf", footer_size)
            except:
                self.footer_font = ImageFont.load_default()

        # Get reference to the main event loop for cross-thread async calls
        loop = asyncio.get_event_loop()

        # Navigation callbacks
        async def on_up():
            self.move_up()

        async def on_down():
            self.move_down()

        async def on_select():
            """Handle selection of current menu option"""
            if self.options and 0 <= self.current_index < len(self.options):
                selected_option = self.options[self.current_index]
                print(f"[MENU] Selected: {selected_option.label}")
                # Execute the callback if present
                await selected_option.execute()

        # Register button handlers
        self.display.on_up = lambda: asyncio.run_coroutine_threadsafe(on_up(), loop)
        self.display.on_down = lambda: asyncio.run_coroutine_threadsafe(on_down(), loop)
        self.display.on_center = lambda: asyncio.run_coroutine_threadsafe(on_select(), loop)
        self.display.on_right = lambda: asyncio.run_coroutine_threadsafe(on_select(), loop)

    async def loop(self):
        """Main render loop"""
        # Create display image
        img = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(img)

        # Render all sections
        self.draw_header(draw)
        self.draw_menu_items(draw)
        self.draw_footer(draw)

        # Update display
        self.display.draw(img)

        # Refresh rate (can be slower than shot_profile since no live data)
        await asyncio.sleep(0.05)  # 20Hz
