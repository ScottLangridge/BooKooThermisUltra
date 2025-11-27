# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmartScaleIntegration is a Python project for integrating with BooKoo smart scales via Bluetooth Low Energy (BLE). The project includes hardware simulation capabilities for testing without physical hardware.

## Architecture

The codebase is organized into three main components:

### 1. Scale Integration (`Scale/`)
- **BookooScale.py**: BLE interface for BooKoo smart scales
  - Uses `bleak` library for BLE communication
  - Communicates via two UUIDs: WEIGHT_UUID (0000ff11...) for reading weight data, COMMAND_UUID (0000ff12...) for sending commands
  - Async-based connection management and continuous weight polling
  - Command methods: tare, timer start/stop/reset, combined tare+timer start
  - Weight data is parsed from 20-byte packets with checksum validation
  - Timer functionality is tracked but not fully implemented (read_time() raises NotImplementedError)
- **scale_poc.py**: Proof-of-concept demonstrating scale connection and basic operations

### 2. UI Simulation (`UI/`)
- **Simulator.py**: Flask-based hardware simulator for embedded device development
  - Provides a 240x240 pixel display simulation accessible via web browser at `http://localhost:5000/display`
  - Accepts PIL images via `draw()` method
  - Simulates 7 hardware buttons: D-pad (up/down/left/right/center) + A/B buttons
  - Callbacks: `on_up`, `on_down`, `on_left`, `on_right`, `on_center`, `on_a`, `on_b`
  - Runs Flask server in daemon thread for non-blocking operation
  - Updates screen every second via JavaScript polling
- **simulator_poc.py**: Proof-of-concept showing button handling and display updates

### 3. Shot Logging (`ShotLogger.py`)
- Work-in-progress espresso shot logging functionality
- Tracks weight in (g_in), weight out (g_out), and timing for espresso shots
- Integrates with BookooScale for automated shot tracking
- Note: Contains syntax error on line 31 (`self.self.scale`)

## Running the Code

### Run Scale Integration POC
```bash
python Scale/scale_poc.py
```
Requires a BooKoo scale to be discoverable via Bluetooth.

### Run UI Simulator POC
```bash
python UI/simulator_poc.py
```
Then open browser to `http://localhost:5000/display` to interact with the simulated hardware.

## Dependencies

The project uses a virtual environment (`venv/`) and requires:
- `bleak` - Bluetooth Low Energy library for scale communication
- `flask` - Web framework for UI simulation
- `pillow` (PIL) - Image manipulation for simulator display

Install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install bleak flask pillow
```

## Development Notes

### Async Pattern for Scale Operations
All scale communication must use `async`/`await` patterns:
```python
scale = BookooScale()
await scale.establish_connection()
await scale.send_tare()
weight = scale.read_weight()  # This is synchronous
await scale.disconnect()
```

### Simulator Integration Pattern
The simulator runs in a background thread and uses callback-based event handling:
```python
sim = Simulator()
sim.on_up = lambda: print("UP pressed")
img = Image.new("RGB", (240, 240), "white")
# Draw to img...
sim.draw(img)
```

### Import Paths
When running from repository root, use relative imports within subdirectories. POC files in `Scale/` and `UI/` import from their respective modules (e.g., `from BookooScale import BookooScale`).

## Known Issues

- ShotLogger.py line 31: `self.self.scale.timer_stop()` should be `self.scale.timer_stop()`
- Timer tracking in BookooScale is not fully implemented (`_time` field exists but `read_time()` raises NotImplementedError)
- Multi-device BooKoo scale discovery is unhandled