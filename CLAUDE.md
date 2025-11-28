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
   - `IO Devices/IOController.py`: Abstract base class for display hardware (240x240 display, 7 buttons: up/down/left/right/center/A/B)
   - `IO Devices/VirtualIOController.py`: Flask-based web simulator for development without physical hardware
     - Runs on http://0.0.0.0:5000/display
     - Auto-refreshes display at 1Hz, provides virtual button interface

2. **Framework Layer** (`screens/base_firmware.py`)
   - `BaseFirmware`: Async base class providing common functionality for screen applications
   - Handles scale connection with infinite retry
   - Manages hardware initialization (scale + display)
   - Provides splash screen utility
   - Subclasses implement `setup()` and `loop()` methods

3. **Application Layer** (`screens/`)
   - `simple_scale/simple_scale.py`: Basic weight display with timer controls (A: start/stop timer, B: tare)
   - `shot_profile/shot_profile.py`: Espresso shot profiling with real-time graphing
     - Graphs weight vs time with dynamic axis scaling
     - A button: start/stop recording
     - B button: reset timer and clear graph
     - Updates at 10Hz
     - Displays live timer and weight readouts

### Key Design Patterns

- **Async/Await**: All scale communication and main loops are async
- **Event Callbacks**: Button handlers use `asyncio.run_coroutine_threadsafe()` to bridge Flask's threading model with asyncio
- **Hardware Abstraction**: IOController interface allows swapping between real hardware and virtual simulator

## Development Commands

### Running Applications

```bash
# Run the simple scale firmware
python screens/simple_scale/simple_scale.py

# Run the shot profiling firmware
python screens/shot_profile/shot_profile.py

# Run proof-of-concept demos
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
- All screen applications inherit from `BaseFirmware`
- Display images must be exactly 240x240 pixels (RGB mode)
- Button callbacks run in Flask's thread context, use `asyncio.run_coroutine_threadsafe()` for async operations
- Scale discovery looks for devices with names starting with "bookoo" (case-insensitive)
- Weight data includes checksum validation and sign handling
- Path manipulation in screen apps uses `sys.path.append(str(Path(__file__).parent.parent))` to enable imports

## Dependencies

Core packages (Python 3.10):
- `bleak==1.1.1`: Bluetooth Low Energy communication
- `flask==3.1.2`: Virtual display web server
- `pillow==12.0.0`: Image generation for display
- `pytest==9.0.1`: Testing framework
- `pytest-asyncio==1.3.0`: Async test support
