import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

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
        # Try common Windows fonts (60pt is 5x bigger than default ~12pt)
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

    # Show splash screen while connecting
    show_splash(display, "Connecting...", "blue")

    # Connect to scale
    print("Connecting to scale...")
    if not await scale.establish_connection():
        print("Failed to connect to scale")
        show_splash(display, "Connection\nFailed", "red")
        # Keep error on screen for a bit before exiting
        await asyncio.sleep(3)
        return

    print("Connected! Starting display loop...")

    # Load font for weight display
    weight_font = None
    try:
        weight_font = ImageFont.truetype("arial.ttf", 80)
    except:
        try:
            weight_font = ImageFont.truetype("Arial.ttf", 80)
        except:
            weight_font = ImageFont.load_default()

    try:
        # Main loop: read weight and update display
        while True:
            # Get current weight
            weight = scale.read_weight()

            # Create display image
            img = Image.new("RGB", (240, 240), "white")
            draw = ImageDraw.Draw(img)

            # Draw weight in center with large font
            if weight is not None:
                weight_text = f"{weight:.1f}g"
                draw.text((120, 120), weight_text, fill="black", anchor="mm", font=weight_font)
            else:
                draw.text((120, 120), "No reading", fill="red", anchor="mm", font=weight_font)

            # Update display
            display.draw(img)

            # Update at 10Hz
            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await scale.disconnect()


if __name__ == "__main__":
    asyncio.run(main())