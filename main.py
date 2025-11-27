from PIL import Image, ImageDraw, ImageFont
from Simulator import Simulator
import time

# Initialize the simulator
sim = Simulator()

# Track button presses
last_button = "None"
button_history = []

def update_display():
    """Update the display with current button state"""
    img = Image.new("RGB", (240, 240), "white")
    draw = ImageDraw.Draw(img)

    # Show current time
    draw.text((10, 10), f"Time: {time.strftime('%H:%M:%S')}", fill="black")

    # Show last button pressed
    draw.text((10, 40), f"Last Button: {last_button}", fill="blue")

    # Show button history (last 5)
    draw.text((10, 70), "Recent:", fill="black")
    for i, btn in enumerate(button_history[-5:]):
        draw.text((10, 90 + i * 20), f"  {btn}", fill="gray")

    sim.draw(img)

def on_button(name):
    """Handle button press"""
    global last_button
    last_button = name
    button_history.append(name)
    print(f"{name} pressed")
    update_display()

# Register button callbacks
sim.on_up = lambda: on_button("UP")
sim.on_down = lambda: on_button("DOWN")
sim.on_left = lambda: on_button("LEFT")
sim.on_right = lambda: on_button("RIGHT")
sim.on_center = lambda: on_button("CENTER")
sim.on_a = lambda: on_button("A")
sim.on_b = lambda: on_button("B")

# Initial display
update_display()

# Update screen every second to refresh time
while True:
    update_display()
    time.sleep(1)
