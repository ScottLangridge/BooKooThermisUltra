# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmartScaleIntegration is a Python application that interfaces with BooKoo Bluetooth smart scales and displays data on a 240x240 pixel TFT display (Adafruit 1.3" Color TFT Bonnet). The project provides a menu-driven firmware system with multiple applications for espresso shot profiling and basic scale functions.

## Environment and File Path Handling

**CRITICAL: This project runs on Windows but uses a Unix shell (Git Bash/WSL)**

When interacting with files and paths:
- The Bash tool runs a Unix shell, NOT Windows cmd/PowerShell
- ALWAYS use Unix-style commands: `ls`, `find`, `rm`, `rmdir`, etc. (NOT `dir`, `del`)
- ALWAYS use forward slashes in paths: `src/drivers/Scale/BookooScale.py`
- Backslashes in paths may appear in output but use forward slashes in commands
- Prefer platform-agnostic tools when possible: Glob, Grep, Read, Edit, Write
- Only use Bash for operations that require shell execution (git, python, pytest, etc.)

**Examples of correct path usage:**
- ✅ `find src -type f -name "*.py"` (Unix command)
- ✅ `rm -r examples/old` (Unix command)
- ✅ `git mv src/old/file.py src/new/file.py` (forward slashes)
- ❌ `dir /B src\drivers` (Windows command - will fail)
- ❌ `del src\file.py` (Windows command - will fail)

## Development Commands

### Running Applications

All applications should be run from the project root directory. The code uses `sys.path.append()` to configure imports.

```bash
# Run the main application (recommended - full menu system)
python -m src.firmware.main

# Run individual screens for testing (bypasses menu)
python -m src.firmware.screens.simple_scale
python -m src.firmware.screens.shot_profile

# Alternative: Set PYTHONPATH manually (if needed)
# On Windows Git Bash/WSL:
PYTHONPATH=. python src/firmware/main.py
```

### Virtual Display

When running any screen application, access the virtual display at:
- **http://localhost:5000/display**

The virtual display auto-refreshes at 1Hz and provides:
- Visual representation of the 240x240 screen
- Clickable buttons for interaction (UP/DOWN/LEFT/RIGHT/CENTER/A/B)
- Keyboard controls (arrow keys, spacebar for CENTER, 'a'/'b' for A/B buttons)

### Testing

```bash
# Run tests with pytest
python -m pytest

# Run tests with verbose output
python -m pytest -v
```

## Architecture

The application uses a **three-layer architecture** with a centralized screen management system.

### Layer 1: Driver Layer (`src/drivers/`)

Hardware abstraction for Bluetooth scale and display device.

#### BookooScale (`src/drivers/Scale/BookooScale.py`)

Bluetooth Low Energy (BLE) driver for BooKoo scales using the bleak library.

**Key characteristics:**
- Discovers devices with names starting with "bookoo" (case-insensitive)
- Weight UUID: `0000ff11-0000-1000-8000-00805f9b34fb`
- Command UUID: `0000ff12-0000-1000-8000-00805f9b34fb`
- Maintains local timer state synchronized with scale hardware
- Calculates flowrate (g/s) from weight history with moving average smoothing

**Timer state management:**
- Cannot start timer if already running
- Cannot start timer if there's accumulated time (must reset first)
- Cannot reset timer while running (must stop first)

**Flowrate calculation:**
- Maintains rolling history of last 50 weight measurements (~5 seconds at 10Hz)
- Calculates instantaneous flowrate between consecutive measurements
- Applies moving average smoothing (window size: 5) to reduce noise
- Returns flowrate in grams per second (g/s)

**Async methods:**
- `establish_connection()`: Discover and connect to scale
- `send_tare()`: Zero the scale
- `send_timer_start()`: Start timer (validates state)
- `send_timer_stop()`: Stop timer and accumulate elapsed time
- `send_timer_reset()`: Reset timer (validates state)
- `send_tare_and_timer_start()`: Combined tare and timer start
- `disconnect()`: Disconnect from scale

**Read methods (synchronous):**
- `read_weight()`: Get current weight in grams
- `read_time()`: Get timer value in seconds (calculated from local state)
- `read_flowrate()`: Get current flowrate in g/s
- `is_timer_running()`: Check timer state
- `is_connected()`: Check connection state

#### IOController (`src/drivers/IODevices/IOController.py`)

Abstract base class representing the display hardware interface (240x240 display, 7 buttons).

**Button callbacks (set these to handle button events):**
- `on_up`, `on_down`, `on_left`, `on_right`, `on_center`, `on_a`, `on_b`

**Abstract method:**
- `draw(img: Image.Image)`: Display a PIL Image (must be exactly 240x240 pixels)

#### VirtualIOController (`src/drivers/IODevices/VirtualIOController.py`)

Flask-based web simulator for development without physical hardware.

**Key characteristics:**
- Runs Flask server on http://0.0.0.0:5000/display in daemon thread
- Auto-refreshes display at 1Hz via JavaScript
- Provides clickable button interface and keyboard controls
- Thread-safe: Button callbacks execute in Flask's thread context

**Important for async callbacks:**
Button handlers run in Flask's thread, not the asyncio event loop. Use `asyncio.run_coroutine_threadsafe()` to schedule async operations:
```python
loop = asyncio.get_event_loop()
self.display.on_a = lambda: asyncio.run_coroutine_threadsafe(on_button_a(), loop)
```

### Layer 2: Framework Layer (`src/firmware/screens/`)

Core framework providing screen lifecycle management and navigation.

#### ScreenManager (`src/firmware/screens/screen_manager.py`)

Central orchestrator for application flow and screen transitions.

**Responsibilities:**
- Initializes hardware once (BookooScale and VirtualIOController)
- Manages connection phase via ConnectionScreen
- Runs main menu loop
- Switches between screens via `switch_screen(screen_class, *args, **kwargs)`
- Handles cleanup on exit (disconnects from scale)

**Control flow:**
1. Create hardware instances (shared across all screens)
2. Show ConnectionScreen until scale connects
3. Enter menu loop:
   - Show menu, wait for selection
   - If screen selected, run it until it calls `stop()`
   - Return to menu
4. On "Exit" selection, cleanup and terminate

**Hardware singleton pattern:**
Hardware is created once in `__init__` and passed to all screens via dependency injection. Screens never create their own hardware instances.

#### BaseScreen (`src/firmware/screens/base_screen.py`)

Async base class providing common functionality for all screen applications.

**Constructor signature:**
```python
def __init__(self, scale: BookooScale, display: IOController)
```

**Lifecycle methods:**
- `setup()`: Override to initialize screen-specific resources (fonts, button callbacks, etc.)
- `loop()`: Override to implement main application loop (called repeatedly until `stop()`)
- `run()`: Framework method that calls `setup()`, then loops `loop()` until `running=False`
- `stop()`: Call this to signal the screen should exit and return control to ScreenManager

**Utility methods:**
- `show_splash(message, color="black")`: Display centered text message (supports multi-line with `\n`)

**Screen lifecycle pattern:**
```python
class MyScreen(BaseScreen):
    async def setup(self):
        # Initialize fonts, button callbacks, state
        loop = asyncio.get_event_loop()
        self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(self.on_left(), loop)

    async def loop(self):
        # Main application logic, runs repeatedly
        # Draw to display, read from scale, etc.
        await asyncio.sleep(0.1)  # Control update rate

    async def on_left(self):
        self.stop()  # Return control to ScreenManager
```

#### ConnectionScreen (`src/firmware/screens/connection_screen.py`)

Dedicated screen for scale connection with visual feedback.

**Key characteristics:**
- Not a subclass of BaseScreen (has different lifecycle)
- Shows "Connecting...", "Connected!", or "Connection Failed" splash screens
- Infinite retry loop until connection succeeds
- `run_until_connected()`: Blocks until scale connection established

**Usage:**
Used once at application startup. After this returns, scale is connected and ready for use.

#### MenuScreen (`src/firmware/screens/menu/menu_screen.py`)

Generic paginated menu renderer with header, footer, and configurable layout.

**Constructor parameters:**
- `title`: Menu title displayed in header
- `options`: List of MenuOption objects
- `items_per_page`: Number of visible options (default: 5)
- `header_height`: Fixed height for title section (default: 40)
- `footer_height`: Fixed height for page indicator (default: 30)

**Navigation:**
- UP/DOWN buttons: Navigate through options (auto-pages when scrolling beyond visible items)
- CENTER or RIGHT buttons: Select current option (both work identically)

**Visual layout:**
- Header: Title centered
- Menu area: Options with highlight, automatically paged
- Footer: Page indicator ("page 1/3")
- Font sizes auto-calculated based on layout dimensions

#### MenuOption (`src/firmware/screens/menu/menu_option.py`)

Represents a single selectable menu item.

**Constructor parameters:**
- `label`: Display text
- `icon`: Right-side decoration (default: ">")
- `callback`: Action to invoke (can be sync function, async function, or lambda)

**Key method:**
- `execute()`: Async method that calls the callback (handles both sync and async via `inspect.iscoroutinefunction()`)

**Callback patterns:**
```python
# Sync callback
def select_option():
    manager.selected_screen = SomeScreen
    manager.current_screen.stop()

# Async callback
async def reconnect():
    await manager.show_connection_screen()

MenuOption("Label", callback=select_option)
MenuOption("Reconnect", callback=reconnect)
```

### Layer 3: Application Layer (`src/firmware/screens/`)

User-facing screen applications.

#### SimpleScale (`src/firmware/screens/simple_scale.py`)

Basic weight display with timer controls.

**Features:**
- Large centered weight display
- Button hints at bottom
- A button: start/stop timer
- B button: tare
- LEFT button: return to menu

**Update rate:** 10Hz (0.1s sleep in loop)

#### ShotProfile (`src/firmware/screens/shot_profile.py`)

Espresso shot profiling with dual-axis real-time graphing.

**Features:**
- Dual-axis graph: weight (blue, left Y-axis) and flowrate (red, right Y-axis)
- Dynamic axis auto-scaling (expands during shot, optimizes after)
- Three-box info display at bottom: Time (s), Flow (g/s), Weight (g)
- A button: tare and start recording
- B button: reset timer and clear graph data
- LEFT button: return to menu

**Update rate:** 10Hz (0.1s sleep in loop)

**Graph layout:**
- Graph area: 240x180 pixels (top section)
- Info boxes: 240x60 pixels (bottom section, 3 boxes of 80x60 each)
- Padding: Asymmetric to accommodate axis labels on both sides
- Tick marks and labels auto-calculated for readability

**Auto-scaling behavior:**
- During recording: Axes expand if data exceeds current range (never shrink)
- After recording: Axes optimize to fit data with 10% buffer

## Key Design Patterns

### Async/Await Throughout
All scale communication and main loops are async. Screen lifecycle methods (`setup()`, `loop()`) are async.

### Dependency Injection
Screens receive hardware instances (scale, display) via constructor. Hardware is created once by ScreenManager and shared across all screens.

### Hardware Singleton
Scale and display are initialized once at application startup and reused. Prevents multiple Bluetooth connections and Flask servers.

### Voluntary Control Return
Screens don't know about ScreenManager. They call `self.stop()` to signal they're done, and their `run()` method returns control to the caller.

### Separation of Concerns
- Connection logic isolated in ConnectionScreen (not repeated in every screen)
- Menu system is generic and reusable
- Each screen focuses only on its display/interaction logic

### Cross-Thread Event Handling
Flask button callbacks run in different thread than asyncio event loop. Bridge with `asyncio.run_coroutine_threadsafe()`:
```python
loop = asyncio.get_event_loop()
async def async_handler():
    await self.scale.send_tare()

self.display.on_a = lambda: asyncio.run_coroutine_threadsafe(async_handler(), loop)
```

### Hardware Abstraction
IOController interface allows swapping between VirtualIOController (development) and real hardware implementation (production).

## Application Control Flow

```
main.py
  └─> ScreenManager.start()
      ├─> Phase 1: Connection
      │   └─> ConnectionScreen.run_until_connected()
      │       └─> [Blocks until scale connected]
      │
      └─> Phase 2: Main Loop (while running)
          ├─> show_menu()
          │   ├─> MenuScreen with options
          │   ├─> User navigates with UP/DOWN
          │   ├─> User selects with CENTER/RIGHT
          │   └─> Callback sets selected_screen, calls stop()
          │
          └─> if selected_screen:
              └─> switch_screen(selected_screen)
                  ├─> Instantiate screen with (scale, display)
                  ├─> screen.run()
                  │   ├─> screen.setup()
                  │   └─> while running: screen.loop()
                  └─> [Blocks until screen.stop() called]
```

When user presses LEFT in an application, it calls `self.stop()`, which causes `run()` to return, giving control back to ScreenManager, which shows the menu again.

## Important Implementation Details

### Display Images
- Must be exactly 240x240 pixels (RGB mode)
- Use PIL Image, ImageDraw, ImageFont for rendering
- Call `display.draw(img)` to update screen

### Font Loading Pattern
```python
try:
    font = ImageFont.truetype("arial.ttf", size)
except:
    try:
        font = ImageFont.truetype("Arial.ttf", size)
    except:
        font = ImageFont.load_default()
```
Case sensitivity varies by OS. Always provide fallback to default font.

### Import Path Configuration
Files use `sys.path.append(str(Path(__file__).parent.parent))` to enable imports from parent directories. This allows running individual screens standalone for testing.

### Weight Data Protocol
Scale weight data includes:
- Checksum validation (XOR of first 19 bytes)
- Sign handling (byte 6: 43=positive, else negative)
- 24-bit raw value (bytes 7-9) divided by 100 for grams

### Button Event Threading
Button callbacks execute in Flask's thread (not asyncio event loop). Always use `asyncio.run_coroutine_threadsafe()` for async operations triggered by buttons.

### Menu Callback Pattern
Menu callbacks typically:
1. Set `manager.selected_screen` to the desired screen class
2. Call `manager.current_screen.stop()` to exit menu
3. Control returns to ScreenManager, which runs the selected screen

Example:
```python
def select_simple_scale():
    self.selected_screen = SimpleScale
    self.current_screen.stop()

MenuOption("Simple Scale", callback=select_simple_scale)
```

## Dependencies

Core packages (Python 3.10.2):
- `bleak==1.1.1`: Bluetooth Low Energy communication with BooKoo scales
- `flask==3.1.2`: Virtual display web server for development
- `pillow==12.0.0`: Image generation and rendering for 240x240 display
- `pytest==9.0.1`: Testing framework
- `pytest-asyncio==1.3.0`: Async test support for asyncio-based code

## File Structure

```
src/
├── drivers/                    # Hardware abstraction layer
│   ├── IODevices/
│   │   ├── IOController.py            # Abstract base class for display
│   │   └── VirtualIOController.py     # Flask-based simulator
│   └── Scale/
│       └── BookooScale.py             # BLE scale driver
│
└── firmware/
    ├── main.py                        # Application entry point
    └── screens/                       # Screen framework and applications
        ├── base_screen.py             # Base class for all screens
        ├── connection_screen.py       # Scale connection handler
        ├── screen_manager.py          # Central orchestrator
        ├── simple_scale.py            # Basic scale screen
        ├── shot_profile.py            # Shot profiling screen
        └── menu/
            ├── menu_screen.py         # Generic menu renderer
            └── menu_option.py         # Menu item representation

examples/                       # Standalone MVP examples (not used in main app)
```

## Adding a New Screen

To add a new screen application:

1. **Create screen class** inheriting from `BaseScreen`:
```python
from src.firmware.screens.base_screen import BaseScreen

class MyScreen(BaseScreen):
    async def setup(self):
        # Initialize resources, setup button callbacks
        loop = asyncio.get_event_loop()
        self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(
            self.on_left(), loop
        )

    async def loop(self):
        # Main application logic
        await asyncio.sleep(0.1)

    async def on_left(self):
        self.stop()  # Return to menu
```

2. **Register in ScreenManager** (`src/firmware/screens/screen_manager.py`):
```python
from src.firmware.screens.my_screen import MyScreen

# In show_menu():
def select_my_screen():
    self.selected_screen = MyScreen
    self.current_screen.stop()

options = [
    # ... existing options
    MenuOption("My Screen", callback=select_my_screen),
    # ... rest of options
]
```

3. **Test standalone** (optional):
```python
if __name__ == "__main__":
    async def main():
        from src.drivers.IODevices.VirtualIOController import VirtualIOController
        from src.firmware.screens.connection_screen import ConnectionScreen

        scale = BookooScale()
        display = VirtualIOController()

        connection_screen = ConnectionScreen(display, scale)
        await connection_screen.run_until_connected()

        app = MyScreen(scale, display)
        await app.run()

        await scale.disconnect()

    asyncio.run(main())
```

Then run: `python -m src.firmware.screens.my_screen`
