import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.firmware.screens.screen import Screen
from src.drivers.Scale.BookooScale import BookooScale
from src.drivers.IODevices.IOController import IOController


class ConnectionScreen(Screen):
    """Dedicated screen for scale connection with visual feedback"""

    def __init__(self, display: IOController, scale: BookooScale):
        """
        Initialize connection screen

        Args:
            display: IOController instance for visual feedback
            scale: BookooScale instance (not yet connected)
        """
        super().__init__(display)
        self.scale = scale

    async def attempt_connection(self) -> bool:
        """
        Single connection attempt with visual feedback

        Returns:
            True if connection succeeded, False otherwise
        """
        self.show_splash("Connecting...", "blue")
        print("Connecting to scale...")

        connected = await self.scale.establish_connection()

        if not connected:
            print("Failed to connect to scale")
            self.show_splash("Connection\nFailed", "red")
            await asyncio.sleep(1)
        else:
            print("Connected!")
            self.show_splash("Connected!", "green")
            await asyncio.sleep(0.5)

        return connected

    async def run_until_connected(self):
        """
        Connect with infinite retry (non-blocking for transitions)

        This method blocks until connection succeeds, providing visual feedback
        for each attempt. When it returns, the scale is connected and ready.
        """
        try:
            while True:
                if await self.attempt_connection():
                    return  # Success - caller can transition to next screen
        except KeyboardInterrupt:
            # Allow interrupt to propagate for graceful shutdown
            raise
