import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from drivers.Scale.BookooScale import BookooScale
from drivers.IODevices.VirtualIOController import VirtualIOController
from firmware.screens.connection_screen import ConnectionScreen


class ScreenManager:
    """Manages application flow and screen transitions"""

    def __init__(self):
        """Initialize hardware once for entire application"""
        # Initialize hardware once for entire application
        self.scale = BookooScale()
        self.display = VirtualIOController()
        self.current_screen = None
        self.running = True
        self.selected_screen = None  # Track which screen was selected from menu

    async def show_connection_screen(self) -> bool:
        """
        Show connection screen until connected

        Returns:
            True when connection succeeds
        """
        connection_screen = ConnectionScreen(self.display, self.scale)
        await connection_screen.run_until_connected()
        # When this returns, connection succeeded
        return True

    async def switch_screen(self, screen_class, *args, **kwargs):
        """
        Generic screen switcher - instantiates and runs any screen class
        Blocks until the screen voluntarily returns control.

        Args:
            screen_class: The screen class to instantiate
            *args: Additional positional arguments for screen constructor
            **kwargs: Additional keyword arguments for screen constructor
        """
        # Hardware is always first two arguments
        screen = screen_class(self.scale, self.display, *args, **kwargs)
        self.current_screen = screen

        # Run the screen - blocks until screen calls stop() and returns
        await screen.run()

        # When we get here, the screen has voluntarily returned control

    async def show_menu(self):
        """
        Show main menu and wait for selection.
        Menu callbacks should set self.selected_screen to indicate choice.
        """
        from firmware.screens.menu.menu_screen import MenuScreen
        from firmware.screens.menu.menu_option import MenuOption
        from firmware.screens.simple_scale.simple_scale import SimpleScale
        from firmware.screens.shot_profile.shot_profile import ShotProfile

        # Reset selection
        self.selected_screen = None

        # Define menu options
        # Note: Callbacks will set selected_screen, then stop the menu
        def select_simple_scale():
            self.selected_screen = SimpleScale
            self.current_screen.stop()  # Tell menu to exit

        def select_shot_profile():
            self.selected_screen = ShotProfile
            self.current_screen.stop()

        async def reconnect():
            await self.show_connection_screen()

        def exit_app():
            self.running = False
            self.current_screen.stop()

        options = [
            MenuOption("Simple Scale", callback=select_simple_scale),
            MenuOption("Shot Profile", callback=select_shot_profile),
            MenuOption("Reconnect", callback=reconnect),
            MenuOption("Exit", callback=exit_app),
        ]

        # Run menu - blocks until user makes selection
        await self.switch_screen(MenuScreen, "MAIN MENU", options)

        # When we get here, menu has returned control

    async def start(self):
        """Application entry point - main control loop"""
        # Phase 1: Connect to scale
        await self.show_connection_screen()

        # Phase 2: Main application loop
        while self.running:
            # Show menu and wait for selection
            await self.show_menu()

            # If user selected a screen (not exit), run it
            if self.selected_screen:
                await self.switch_screen(self.selected_screen)
                # When screen returns, loop back to menu

        # Cleanup when exiting
        print("Exiting application...")
        await self.scale.disconnect()
