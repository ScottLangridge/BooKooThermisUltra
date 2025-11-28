import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from firmware.screens.menu.menu_screen import MenuScreen
from firmware.screens.menu.menu_option import MenuOption


# Example callback functions demonstrating different patterns

def simple_scale_callback():
    """Regular synchronous callback"""
    print("[CALLBACK] Starting Simple Scale application...")
    # In the future, this could launch the simple scale firmware


async def shot_profile_callback():
    """Async callback example"""
    print("[CALLBACK] Starting Shot Profile application...")
    await asyncio.sleep(0.1)  # Simulate async operation
    print("[CALLBACK] Shot Profile initialized")
    # In the future, this could launch the shot profile firmware


def settings_callback():
    """Example for settings menu"""
    print("[CALLBACK] Opening settings...")
    # In the future, this could open a sub-menu or settings screen


async def exit_callback():
    """Exit callback that could perform cleanup"""
    print("[CALLBACK] Exiting application...")
    # In the future, this could trigger cleanup and shutdown
    # For now, we just log it


# Create menu options with callbacks
options = [
    MenuOption("Simple Scale", callback=simple_scale_callback),
    MenuOption("Shot Profile", callback=shot_profile_callback),
    MenuOption("Settings", callback=settings_callback),
    MenuOption("Calibration", callback=lambda: print("[CALLBACK] Opening calibration wizard...")),
    MenuOption("About", callback=lambda: print("[CALLBACK] SmartScale v1.0 - BooKoo Integration")),
    MenuOption("Placeholder"),  # No callback
    MenuOption("Exit", callback=exit_callback),
]

# Create menu screen
menu = MenuScreen(
    title="MAIN MENU",
    options=options,
    items_per_page=5,
    header_height=40,
    footer_height=40
)

# Run the menu
if __name__ == "__main__":
    asyncio.run(menu.run())
