import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.firmware.screens.screen import Screen
from src.drivers.Scale.BookooScale import BookooScale
from src.drivers.IODevices.IOController import IOController


class InteractiveScreen(Screen):
    """
    Abstract base class for interactive screens with setup/loop/stop lifecycle

    Interactive screens are the main application screens that users interact
    with via buttons. They follow a lifecycle pattern:
    1. setup() - Initialize resources and button callbacks
    2. loop() - Main application logic (called repeatedly)
    3. stop() - Signal to exit and return to menu

    Subclasses must implement setup() and loop().
    """

    def __init__(self, scale: BookooScale, display: IOController, refresh_rate: float = 0.1):
        """
        Initialize interactive screen with hardware dependencies

        Args:
            scale: Connected BookooScale instance
            display: IOController instance
            refresh_rate: Update frequency in seconds (default: 0.1 = 10Hz)
        """
        super().__init__(display)
        self.scale = scale
        self.running = False
        self.refresh_rate = refresh_rate
        self.event_loop = None  # Event loop reference, set in run()

    def stop(self):
        """
        Signal the screen to stop and return control voluntarily

        Call this method (typically from a button callback) to exit
        the screen and return control to ScreenManager.
        """
        self.running = False

    def bind_button(self, button_name: str, async_callback):
        """
        Bind an async callback to a button safely

        Handles the threading complexity of calling async functions from
        Flask's button callbacks.

        Args:
            button_name: Button name ('a', 'b', 'up', 'down', 'left', 'right', 'center')
            async_callback: Async function to call when button is pressed

        Example:
            self.bind_button('left', self.on_left)
            # Instead of:
            # self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(self.on_left(), loop)
        """
        setattr(
            self.display,
            f'on_{button_name}',
            lambda: asyncio.run_coroutine_threadsafe(async_callback(), self.event_loop)
        )

    async def setup(self):
        """
        Override this method to add setup logic after connection

        This is called once before the loop starts. Use it to:
        - Load fonts
        - Set up button callbacks
        - Initialize screen-specific state

        Note: self.event_loop is already set and available for use

        Example:
            async def setup(self):
                self.font = self.load_font("arial", 80)
                self.bind_button('left', self.on_left)
                self.bind_button('a', self.on_button_a)
        """
        pass

    async def loop(self):
        """
        Override this method to implement the main application loop

        This is called repeatedly while the screen is running. Use it to:
        - Read data from the scale
        - Draw to the display
        - Update application state

        Note: refresh_rate is handled automatically by the framework.
        Do NOT include await asyncio.sleep() in your loop implementation.

        Example:
            async def loop(self):
                weight = self.scale.read_weight()
                # ... draw weight to display ...
                # Sleep is automatic!
        """
        raise NotImplementedError("Subclasses must implement loop()")

    async def run(self):
        """
        Run screen lifecycle until stop() is called

        Framework method that orchestrates the screen lifecycle:
        1. Get event loop reference
        2. Print startup message
        3. Call setup() once
        4. Call loop() repeatedly until running becomes False
        5. Automatically throttle based on refresh_rate

        When this method returns, control goes back to ScreenManager.
        """
        # Get event loop reference for button callbacks
        self.event_loop = asyncio.get_event_loop()

        # Print startup message
        print(f"Starting {self.__class__.__name__}...")

        # Setup screen
        await self.setup()
        self.running = True

        try:
            while self.running:
                await self.loop()
                await asyncio.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            # Stop the screen gracefully, then re-raise to trigger cleanup
            self.running = False
            raise

        # When running becomes False, loop exits and control returns
