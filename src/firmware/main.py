import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from src.firmware.screens.screen_manager import ScreenManager


async def main():
    """Application entry point"""
    manager = ScreenManager()
    await manager.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Cleanup already handled by ScreenManager's finally block
        print("\nApplication terminated by user")
        pass
