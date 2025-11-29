import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.firmware.screens.base_screen import BaseScreen
from src.firmware.screens.menu.menu_screen import MenuScreen
from src.firmware.screens.menu.menu_option import MenuOption
from src.firmware.screens.colorscheme_picker import ColorschemePickerScreen
from src.drivers.Scale.BookooScale import BookooScale
from src.drivers.IODevices.IOController import IOController


class SettingsScreen(BaseScreen):
    """Settings screen that manages internal navigation between settings options"""

    def __init__(self, scale: BookooScale, display: IOController):
        super().__init__(scale, display)
        self.selected_option = None
        self.settings_menu = None

    async def setup(self):
        """Initialize settings screen"""
        print("Starting settings screen...")

    async def loop(self):
        """Main settings navigation loop"""
        import asyncio

        while self.running:
            # Reset selection
            self.selected_option = None

            # Create settings menu
            def select_colorscheme():
                self.selected_option = 'colorscheme'
                self.settings_menu.stop()

            settings_options = [
                MenuOption("Colourscheme", callback=select_colorscheme),
            ]

            # Create settings menu
            self.settings_menu = MenuScreen(self.scale, self.display, "SETTINGS", settings_options)

            # Add LEFT button handler to exit settings menu
            loop = asyncio.get_event_loop()

            async def on_left():
                self.selected_option = None  # No option selected
                self.settings_menu.stop()

            self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(on_left(), loop)

            # Run settings menu
            await self.settings_menu.run()

            # Handle selected option
            if self.selected_option == 'colorscheme':
                # Run colorscheme picker
                picker = ColorschemePickerScreen(self.scale, self.display)
                await picker.run()
                # When picker returns, loop back to show settings menu again
            else:
                # No option selected (user pressed LEFT), exit settings
                self.stop()
                break
