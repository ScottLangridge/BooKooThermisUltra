import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from firmware.screens.screen_manager import ScreenManager


async def main():
    """Application entry point"""
    manager = ScreenManager()
    await manager.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
