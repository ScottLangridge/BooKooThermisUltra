import asyncio
import inspect
from typing import Callable, Optional, Any


class MenuOption:
    """Represents a single menu item with an optional callback"""

    def __init__(self, label: str, icon: str = ">", callback: Optional[Callable] = None):
        """
        Create a menu option

        Args:
            label: The text to display
            icon: Right-side decoration (default: ">")
            callback: Action to invoke when selected. Can be:
                     - A regular function: def my_callback(): ...
                     - An async function: async def my_callback(): ...
                     - A lambda: lambda: print("Selected")
                     - None (no action)
        """
        self.label = label
        self.icon = icon
        self.callback = callback

    async def execute(self) -> Any:
        """
        Execute the callback if present, handling both sync and async callables

        Returns:
            The return value of the callback, or None if no callback is set
        """
        if self.callback is None:
            return None

        # Check if callback is an async function
        if inspect.iscoroutinefunction(self.callback):
            return await self.callback()
        else:
            # Regular synchronous function
            return self.callback()
