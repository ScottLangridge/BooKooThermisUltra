# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmartScaleIntegration is a Python application for interfacing with BooKoo Bluetooth smart scales and displaying data on a 240x240 pixel TFT display (Adafruit 1.3" Color TFT Bonnet). The project provides firmware applications for espresso shot profiling and basic scale functions.

## Architecture

### Three-Layer Architecture

1. **Driver Layer** (`drivers/`)
   - `Scale/BookooScale.py`: Bluetooth Low Energy (BLE) driver for BooKoo scales using bleak library
     - Handles device discovery, connection management, and weight/timer data
     - Maintains local timer state synchronized with scale hardware
     - Weight UUID: `0000ff11-0000-1000-8000-00805f9b34fb`
     - Command UUID: `0000ff12-0000-1000-8000-00805f9b34fb`
   - `IODevices/IOController.py`: Abstract base class for display hardware (240x240 display, 7 buttons: up/down/left/right/center/A/B)
   - `IODevices/VirtualIOController.py`: Flask-based web simulator for development without physical hardware
     - Runs on http://0.0.0.0:5000/display
     - Auto-refreshes display at 1Hz, provides virtual button interface

2. **Framework Layer** (`firmware/screens/`)
   - `base_screen.py`: Contains `BaseScreen` async base class providing common functionality for screen applications
     - Accepts hardware instances (scale, display) via dependency injection
     - Provides lifecycle management with `setup()` and `loop()` methods
     - Provides `stop()` method for voluntary control return to ScreenManager
     - Provides splash screen utility
     - Subclasses implement `setup()` and `loop()` methods
   - `connection_screen.py`: Dedicated screen for scale connection
     - Handles connection with infinite retry and visual feedback
     - Shows "Connecting...", "Connected!", or "Connection Failed" splash screens
     - Used once at application startup
   - `screen_manager.py`: Central orchestrator for application flow
     - Initializes hardware once (shared across all screens)
     - Manages screen transitions via `switch_screen()`
     - Runs connection phase, then enters menu loop
     - Handles cleanup on exit
   - `menu/`: Menu system for navigation between applications
     - `menu_screen.py`: `MenuScreen` class for rendering paginated menus with header/footer
       - Supports up/down/center button navigation
       - Configurable items per page, header/footer heights
       - Auto-paging when scrolling beyond visible items
     - `menu_option.py`: `MenuOption` class representing selectable menu items
       - Supports both sync and async callbacks
       - Configurable label and icon

3. **Application Layer** (`firmware/screens/`)
   - `simple_scale/simple_scale.py`: Basic weight display with timer controls
     - A button: start/stop timer
     - B button: tare
     - LEFT button: return to menu
   - `shot_profile/shot_profile.py`: Espresso shot profiling with real-time graphing
     - Graphs weight vs time with dynamic axis scaling
     - A button: start/stop recording
     - B button: reset timer and clear graph
     - LEFT button: return to menu
     - Updates at 10Hz
     - Displays live timer and weight readouts

### Key Design Patterns

- **Async/Await**: All scale communication and main loops are async
- **Dependency Injection**: Screens receive hardware instances via constructor rather than creating them
- **Separation of Concerns**: Connection logic separated from screen lifecycle management
- **Hardware Singleton**: Scale and display initialized once and shared across all screens
- **Voluntary Control Return**: Screens call `stop()` to return control to ScreenManager
- **Event Callbacks**: Button handlers use `asyncio.run_coroutine_threadsafe()` to bridge Flask's threading model with asyncio
- **Hardware Abstraction**: IOController interface allows swapping between real hardware and virtual simulator

### Application Flow

The application follows this control flow:

1. **Startup** (`firmware/main.py`):
   - ScreenManager creates hardware instances (once)
   - ConnectionScreen handles scale connection with visual feedback
   - Transitions to main menu after successful connection

2. **Menu Loop**:
   - User navigates menu with UP/DOWN buttons
   - User selects screen with CENTER button
   - Selected screen runs until user presses LEFT button
   - Control returns to menu

3. **Screen Lifecycle**:
   - Screen receives hardware via constructor
   - `setup()` initializes screen-specific resources
   - `loop()` runs continuously until `stop()` is called
   - LEFT button calls `stop()` to return control to ScreenManager

4. **Exit**:
   - User selects "Exit" from menu
   - ScreenManager disconnects from scale
   - Application terminates

## Development Commands

### Running Applications

```bash
# Run the main application (recommended)
python firmware/main.py

# Run individual screens for testing
python firmware/screens/simple_scale/simple_scale.py
python firmware/screens/shot_profile/shot_profile.py

# Run proof-of-concept demos
python pocs/menu_poc.py           # Menu system test
python pocs/scale_poc.py          # Scale communication test
python pocs/simulator_poc.py      # Display simulator test
```

### Testing

```bash
# Run tests with pytest
python -m pytest

# Run tests with async support
python -m pytest -v
```

### Virtual Display

When running any screen application, access the virtual display at:
- http://localhost:5000/display

The virtual display will show the current screen output and provide clickable buttons for interaction.

## Hardware Communication

### Scale Commands

The BookooScale driver provides these async methods:
- `establish_connection()`: Discover and connect to scale
- `send_tare()`: Zero the scale
- `send_timer_start()`: Start timer (only if not running and no accumulated time)
- `send_timer_stop()`: Stop timer and accumulate elapsed time
- `send_timer_reset()`: Reset timer (only when stopped)
- `send_tare_and_timer_start()`: Combined tare and timer start
- `read_weight()`: Get current weight in grams
- `read_time()`: Get timer value in seconds
- `is_timer_running()`: Check timer state

### Timer State Management

The scale maintains timer state both on the device and locally. The local state prevents invalid operations:
- Cannot start timer if already running
- Cannot start timer if there's accumulated time (must reset first)
- Cannot reset timer while running (must stop first)

## Important Notes

- Python 3.10+ required
- All screen applications inherit from `BaseScreen` (located in `firmware/screens/base_screen.py`)
- Screens receive hardware via constructor (dependency injection pattern)
- Screens must call `self.stop()` to return control to ScreenManager
- Hardware is initialized once and shared across all screens
- Connection logic is handled by `ConnectionScreen`, not individual screens
- Display images must be exactly 240x240 pixels (RGB mode)
- Button callbacks run in Flask's thread context, use `asyncio.run_coroutine_threadsafe()` for async operations
- Scale discovery looks for devices with names starting with "bookoo" (case-insensitive)
- Weight data includes checksum validation and sign handling
- Path manipulation uses `sys.path.append(str(Path(__file__).parent.parent))` to enable imports from parent directories
- Menu system supports both synchronous and asynchronous callbacks via `inspect.iscoroutinefunction()`

## Dependencies

Core packages (Python 3.10):
- `bleak==1.1.1`: Bluetooth Low Energy communication
- `flask==3.1.2`: Virtual display web server
- `pillow==12.0.0`: Image generation for display
- `pytest==9.0.1`: Testing framework
- `pytest-asyncio==1.3.0`: Async test support
