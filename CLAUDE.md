# SmartScaleIntegration

A Python-based firmware platform for the BooKoo smart espresso scale with display integration. This project provides a modular architecture for creating custom firmware applications that interact with the scale's weight sensor, timer, and display.

## Project Overview

This project enables building interactive applications for a BooKoo Bluetooth scale with a 240x240 display. It provides hardware abstraction layers and a firmware framework for rapid development of scale-based applications.

## Architecture

### Core Components

```
SmartScaleIntegration/
├── firmware/               # Firmware applications
│   ├── base_firmware.py   # Base class for all firmware apps
│   ├── shot_profile/      # Shot profiling application (main feature)
│   │   └── shot_profile.py
│   └── simple_scale/      # Simple weight display app
│       └── simple_scale.py
├── drivers/               # Hardware abstraction layer
│   ├── Scale/            # Scale communication drivers
│   │   ├── BookooScale.py        # Main BLE scale driver
│   │   └── scale_poc.py          # Proof-of-concept
│   └── UI/               # Display interface drivers
│       ├── IOController.py       # Abstract base class
│       └── VirtualIOController.py # Web-based simulator
└── ShotLogger.py         # Shot logging utilities (WIP)
```

## Hardware Drivers

### BookooScale (drivers/Scale/BookooScale.py)

BLE driver for the BooKoo smart scale with comprehensive timer and weight tracking.

**Key Features:**
- Async BLE communication using bleak library
- Auto-discovery of BooKoo devices
- Weight reading via notifications (0.01g precision)
- Timer control (start/stop/reset)
- Local timer state tracking synchronized with scale
- Combined tare+timer start operation

**BLE UUIDs:**
- Weight notifications: `0000ff11-0000-1000-8000-00805f9b34fb`
- Command writes: `0000ff12-0000-1000-8000-00805f9b34fb`

**API Methods:**
- `establish_connection()` - Discover and connect to scale
- `read_weight()` - Get current weight in grams
- `read_time()` - Get timer value in seconds
- `is_timer_running()` - Check timer state
- `send_tare()` - Zero the scale
- `send_timer_start()` - Start timer
- `send_timer_stop()` - Stop timer (accumulates elapsed time)
- `send_timer_reset()` - Reset timer to zero
- `send_tare_and_timer_start()` - Combined operation

**Timer Implementation:**
The driver maintains local timer state synchronized with the scale:
- `_timer_start_time`: Timestamp when timer started
- `_timer_running`: Boolean state flag
- `_timer_elapsed`: Accumulated time when paused

Timer reading is calculated live when running, combining elapsed + current duration.

### IOController (drivers/UI/)

Abstract base class defining the display interface for 240x240 displays with 7 buttons.

**Supported Buttons:**
- D-pad: up, down, left, right, center
- Action buttons: A, B

**Abstract Methods:**
- `draw(img: Image.Image)` - Display a PIL Image (240x240)

**Implementations:**
- `VirtualIOController` - Flask-based web simulator at localhost:5000/display
  - Real-time display updates (1 FPS auto-refresh)
  - Browser-based button controls
  - Development/testing without hardware

## Firmware Framework

### BaseFirmware (firmware/base_firmware.py)

Abstract base class providing common firmware infrastructure.

**Lifecycle Methods:**
1. `__init__()` - Initialize instance variables
2. `run()` - Entry point (handles connection, setup, main loop)
3. `connect_to_scale()` - Auto-retry connection with visual feedback
4. `setup()` - Override for post-connection initialization
5. `loop()` - Override for main application logic (called repeatedly)

**Provided Utilities:**
- `show_splash(message, color)` - Display centered text messages
- Auto-initialized `self.scale` (BookooScale instance)
- Auto-initialized `self.display` (VirtualIOController instance)
- Graceful shutdown on Ctrl+C

**Usage Pattern:**
```python
class MyApp(BaseFirmware):
    async def setup(self):
        # Initialize after connection
        pass

    async def loop(self):
        # Main application logic
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    app = MyApp()
    asyncio.run(app.run())
```

## Firmware Applications

### SimpleScale (firmware/simple_scale/simple_scale.py)

Basic scale application demonstrating core functionality.

**Features:**
- Large weight display (80pt font)
- Timer start/stop with button A
- Tare with button B
- Button hints at bottom
- 10Hz update rate

**Implementation Details:**
- Loads Arial.ttf fonts (falls back to default)
- Uses `asyncio.run_coroutine_threadsafe` for cross-thread button handling
- Displays timer status in button hints

### ShotProfile (firmware/shot_profile/shot_profile.py)

**STATUS: FOUNDATION COMPLETE - MAJOR FEATURE IN DEVELOPMENT**

Espresso shot profiling application with graphing capabilities. This is the primary application being developed.

**Current Implementation (v1):**

**Layout:**
- Top section (180px): Graph area with axes
- Bottom section (60px): Two info boxes
  - Left box: Timer (seconds)
  - Right box: Weight (grams)

**Display Elements:**
- Graph axes with 20px padding
- Vertical Y-axis (left)
- Horizontal X-axis (bottom)
- Border around entire display
- Dividing lines between sections
- Real-time timer and weight display (32pt font)

**Controls:**
- Button A: Start/Stop timer
- Button B: Reset timer

**Code Structure:**
```
ShotProfile class (extends BaseFirmware)
├── __init__()
│   └── Define layout dimensions
├── setup()
│   ├── Load fonts
│   └── Configure button callbacks
├── loop()
│   ├── Create display image
│   ├── draw_graph_axes()
│   ├── draw_info_section()
│   └── Update at 10Hz
├── draw_graph_axes(draw)
│   └── Draw X/Y axes
└── draw_info_section(draw)
    ├── Draw dividing lines
    ├── Read scale values
    └── Display timer and weight
```

**Key Dimensions:**
```python
width = 240
height = 240
graph_height = 180      # Top section
info_height = 60        # Bottom section
graph_padding = 20      # Graph area padding
graph_x = 20           # Graph start X
graph_y = 20           # Graph start Y
graph_w = 200          # Graph width (240 - 2*20)
graph_h = 140          # Graph height (180 - 2*20)
```

**Planned Features (Next Phase):**

The shot profiling feature will be significantly expanded to include:

1. **Data Collection:**
   - Real-time weight/time data points during shot
   - Configurable sample rate
   - Data buffering and storage

2. **Graph Rendering:**
   - Plot weight vs. time curve in graph area
   - Auto-scaling Y-axis based on weight range
   - Time-based X-axis with markers
   - Grid lines for readability
   - Flow rate calculation and overlay

3. **Shot Detection:**
   - Auto-start on weight change
   - Shot completion detection
   - Pre-infusion phase tracking

4. **Profile Management:**
   - Save/load shot profiles
   - Profile comparison overlay
   - Target profile visualization

5. **Advanced UI:**
   - Multi-screen navigation
   - Profile selection menu
   - Settings screen
   - Historical shot review

6. **Data Export:**
   - CSV export of shot data
   - Profile sharing
   - Statistical analysis

**Development Notes:**
- Graph area (200x140px usable space) is ready for plotting
- Timer and weight are already being read at 10Hz
- Button infrastructure supports additional controls
- Consider data structure for time-series storage
- May need optimization for real-time plotting performance

## Development Workflow

### Running Applications

**Shot Profile App:**
```bash
cd firmware/shot_profile
python shot_profile.py
```

**Simple Scale App:**
```bash
cd firmware/simple_scale
python simple_scale.py
```

### Using Virtual Display

1. Start any firmware application
2. Open browser to `http://localhost:5000/display`
3. Use on-screen buttons to interact
4. Display updates automatically at 1 FPS

### Hardware Requirements

**BLE Scale:**
- BooKoo smart scale (BLE enabled)
- Must be in range and powered on
- Auto-discovered by name prefix "bookoo" (case-insensitive)

**Display (for production):**
- Adafruit 1.3" Color TFT Bonnet
- 240x240 ST7789 display
- 7 buttons (5-way joystick + 2 action)

### Development Tips

**Cross-Thread Async Pattern:**
Button callbacks run in Flask thread but need to call async scale methods. Use:
```python
loop = asyncio.get_event_loop()
self.display.on_a = lambda: asyncio.run_coroutine_threadsafe(
    async_handler(), loop
)
```

**Font Loading:**
Try multiple paths with fallback:
```python
try:
    font = ImageFont.truetype("arial.ttf", size)
except:
    try:
        font = ImageFont.truetype("Arial.ttf", size)
    except:
        font = ImageFont.load_default()
```

**Update Rate:**
All firmware apps use 10Hz (0.1s sleep) for consistent UX.

## Dependencies

**Required Packages:**
- `bleak` - Async BLE library
- `Pillow` - Image manipulation and drawing
- `Flask` - Web server for virtual display
- `asyncio` - Async/await support (stdlib)

**Python Version:**
- Python 3.7+ (requires async/await)

## Known Issues & TODOs

**ShotLogger.py:**
- Incomplete implementation (line 31 has syntax error)
- Not integrated with current architecture
- Needs refactor to work with BaseFirmware

**Timer Synchronization:**
- Scale has internal timer, driver tracks locally
- Potential for drift if scale is reset externally
- Reset command validates timer isn't running before allowing

**Font Availability:**
- Arial.ttf may not exist on all systems
- Fallback to default font has poor quality
- Consider bundling font file

**BLE Stability:**
- No automatic reconnection on connection loss
- Single device support only (no multi-scale)

## Recent Changes

Based on git history:
- `9719801` - Added empty graph and controls to shot_profile.py (current state)
- `a36b86a` - Added timer handling
- `6aee23d` - Refactored firmware apps to use BaseFirmware superclass
- `6efc974` - Created shot profile placeholder
- `ef4c109` - Added interactive scale demo with button controls

## Future Directions

**Short Term:**
1. Implement data collection in shot_profile.py
2. Add real-time graph plotting
3. Auto-start shot detection
4. Profile saving/loading

**Long Term:**
1. Hardware IOController implementation
2. Multiple firmware apps (pre-infusion timer, ratio calculator, etc.)
3. Web API for remote monitoring
4. Mobile app integration
5. Cloud profile sync

## Code Style Notes

- Async/await throughout
- Type hints minimal (add for public APIs)
- Comments focus on "why" not "what"
- 4-space indentation
- Private methods prefixed with `_`
- Constants in UPPER_CASE
