import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from PIL import Image
from base_firmware import BaseFirmware


class ShotProfile(BaseFirmware):
    """Shot profile graphing application"""

    async def setup(self):
        """Initialize after connection"""
        print("Starting shot profile...")

        # Show blank screen
        img = Image.new("RGB", (240, 240), "white")
        self.display.draw(img)

    async def loop(self):
        """Main loop - currently just waits"""
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    app = ShotProfile()
    asyncio.run(app.run())