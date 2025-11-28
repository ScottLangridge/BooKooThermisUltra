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

    print("Connected! Starting display loop...")

    # Load fonts for display
    weight_font = None
    hint_font = None
    try:
        weight_font = ImageFont.truetype("arial.ttf", 80)
        hint_font = ImageFont.truetype("arial.ttf", 16)
    except:
        try:
            weight_font = ImageFont.truetype("Arial.ttf", 80)
            hint_font = ImageFont.truetype("Arial.ttf", 16)
        except:
            weight_font = ImageFont.load_default()
            hint_font = ImageFont.load_default()

    # Track timer state
    timer_running = False

    # Get reference to the main event loop for cross-thread async calls
    loop = asyncio.get_event_loop()

    # Button A: Start/Stop Timer
    async def on_button_a():
        nonlocal timer_running
        if timer_running:
            await scale.send_timer_stop()
            timer_running = False
            print("Timer stopped")
        else:
            await scale.send_timer_start()
            timer_running = True
            print("Timer started")

    # Button B: Tare
    async def on_button_b():
        await scale.send_tare()
        print("Tared")

    # Set up button callbacks using run_coroutine_threadsafe for cross-thread async
    display.on_a = lambda: asyncio.run_coroutine_threadsafe(on_button_a(), loop)
    display.on_b = lambda: asyncio.run_coroutine_threadsafe(on_button_b(), loop)

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

            # Draw button hints at bottom
            timer_status = "running" if timer_running else "stopped"
            hint_text = f"A: Timer ({timer_status})  |  B: Tare"
            draw.text((120, 220), hint_text, fill="gray", anchor="mm", font=hint_font)

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