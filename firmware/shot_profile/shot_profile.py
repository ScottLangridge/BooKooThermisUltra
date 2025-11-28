import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from PIL import Image, ImageDraw, ImageFont
from drivers.Scale.BookooScale import BookooScale
from drivers.UI.VirtualIOController import VirtualIOController


def show_splash(display, message, color="black"):
    """Display a message on the screen"""
    img = Image.new("RGB", (240, 240), "white")
    draw = ImageDraw.Draw(img)

    # Try to load a large font, fall back to default if not available
    font = None
    try:
        # Try common Windows fonts
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        try:
            font = ImageFont.truetype("Arial.ttf", 30)
        except:
            # If no TrueType font available, use default (will be smaller)
            font = ImageFont.load_default()

    # Split message into lines for multi-line support
    lines = message.split('\n')
    line_height = 70
    start_y = 120 - (len(lines) - 1) * line_height / 2

    for i, line in enumerate(lines):
        y_pos = start_y + i * line_height
        draw.text((120, y_pos), line, fill=color, anchor="mm", font=font)

    display.draw(img)


async def main():
    # Initialize hardware
    scale = BookooScale()
    display = VirtualIOController()

    # Connect to scale with infinite retry
    connected = False
    while not connected:
        show_splash(display, "Connecting...", "blue")
        print("Connecting to scale...")
        connected = await scale.establish_connection()

        if not connected:
            print("Failed to connect to scale, retrying...")
            show_splash(display, "Connection\nFailed", "red")
            await asyncio.sleep(1)

    print("Connected! Starting shot profile...")

    # Show blank screen
    img = Image.new("RGB", (240, 240), "white")
    display.draw(img)

    try:
        # Main loop: keep running with blank display
        while True:
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await scale.disconnect()


if __name__ == "__main__":
    asyncio.run(main())