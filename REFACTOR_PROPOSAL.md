# Screen Architecture Refactor Proposal

## Current State Analysis

### Problems with Current Architecture

1. **Tight Coupling**: Every screen independently manages scale connection through `BaseScreen.run()`
2. **Redundant Connection**: Each screen connects to the scale when launched, even if already connected
3. **No Separation of Concerns**: Connection logic is mixed with screen lifecycle management
4. **No Screen Transitions**: No mechanism to transition between screens while maintaining connection
5. **Hardware Recreation**: Each screen creates new `BookooScale` and `IOController` instances

### Current Flow
```
BaseScreen.run()
  ├─ Initialize hardware (scale, display)
  ├─ connect_to_scale() [shows "Connecting..." splash]
  ├─ setup()
  └─ loop() [infinite]
```

---

## Quick Comparison: Before vs After

### Before (Current)
```
Each Screen:
  run()
    ├─ Create hardware
    ├─ Connect to scale (splash screens)
    ├─ setup()
    └─ loop() [no exit mechanism]

Adding new screen to menu:
  1. Create screen class
  2. Write launch_new_screen() method in ScreenManager
  3. Add menu option pointing to launch method
```

### After (Proposed)
```
Main Entry Point:
  main.py
    └─ ScreenManager.start()
         ├─ Create hardware (once)
         ├─ ConnectionScreen (dedicated)
         └─ switch_screen(MenuScreen)
              └─ User selects → switch_screen(SelectedScreen)

Each Screen:
  __init__(scale, display)  # Receives hardware
  setup()                    # Screen-specific setup
  loop()                     # Screen-specific logic

Adding new screen to menu:
  1. Create screen class
  2. Add menu option: MenuOption("Name", callback=lambda: self.switch_screen(NewScreen))
```

**Key Improvements:**
- ✅ Hardware created **once** (not per-screen)
- ✅ Connection is a **dedicated phase** (not repeated)
- ✅ **Generic** `switch_screen()` replaces per-screen launch methods
- ✅ Adding screens is **simpler** (1 line vs 3 steps)
- ✅ Visual feedback centralized in ConnectionScreen

---

## Proposed Architecture

### Core Principles

1. **Separation of Concerns**: Connection is a distinct phase, not part of every screen
2. **Hardware Singleton**: Scale and display are initialized once and shared
3. **Screen Transitions**: Screens can transition to other screens without reconnecting
4. **Dependency Injection**: Screens receive hardware instances rather than creating them

### New Component: ConnectionScreen

A dedicated screen that handles the connection phase:

```python
class ConnectionScreen(BaseScreen):
    """Handles scale connection with visual feedback"""

    async def run_connection(self):
        """Connect to scale with retry logic and splash feedback"""
        - Show "Connecting..." splash
        - Attempt connection
        - On failure: Show "Failed" splash, retry
        - On success: Return to caller
```

### Refactored BaseScreen

Remove hardware initialization and connection logic:

```python
class BaseScreen:
    """Base class for screens - receives initialized hardware"""

    def __init__(self, scale: BookooScale, display: IOController):
        """Accept hardware dependencies via constructor"""
        self.scale = scale
        self.display = display

    async def run(self):
        """Run the screen (no connection logic)"""
        await self.setup()
        while True:
            await self.loop()

    # Remove: connect_to_scale()
    # Remove: hardware initialization in run()
```

### New Component: ScreenManager

Manages screen lifecycle and transitions:

```python
class ScreenManager:
    """Coordinates screen transitions and hardware lifecycle"""

    def __init__(self):
        self.scale = BookooScale()
        self.display = VirtualIOController()
        self.current_screen = None

    async def transition_to(self, screen_class, *args, **kwargs):
        """Transition to a new screen"""
        - Stop current screen's loop
        - Instantiate new screen with hardware
        - Start new screen's run()

    async def start(self):
        """Entry point: connect then show menu"""
        - Run ConnectionScreen
        - On success, transition to MenuScreen
```

### New Entry Point: main.py

Single entry point for the entire application:

```python
async def main():
    manager = ScreenManager()
    await manager.start()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Control Flow: How Screens Return Control Voluntarily

### The Key Mechanism

Every screen **voluntarily returns control** to the ScreenManager by calling `self.stop()`, which:
1. Sets `self.running = False`
2. Causes the `while self.running:` loop to exit
3. The `run()` method returns
4. Control goes back to whoever called `await screen.run()`

### Detailed Control Flow

```
1. main.py starts
   └─> ScreenManager.start()

2. ScreenManager runs ConnectionScreen
   await connection_screen.run_until_connected()
   │
   └─> ConnectionScreen loops until connection succeeds
       └─> self.running = False (implicit - loop condition met)
       └─> RETURNS to ScreenManager

3. ScreenManager enters main loop
   while self.running:

4. ScreenManager shows menu
   await show_menu()
   │
   └─> MenuScreen.run()
       │
       └─> User presses UP/DOWN to navigate
       └─> User presses CENTER to select
       └─> Callback executes:
           - Sets manager.selected_screen = SimpleScale
           - Calls self.stop() to exit menu
       └─> RETURNS to ScreenManager with selection

5. ScreenManager launches selected screen
   if self.selected_screen:
       await switch_screen(SimpleScale)
       │
       └─> SimpleScale.run()
           │
           └─> User presses A/B buttons (timer/tare)
           └─> User presses LEFT button
           └─> on_left() calls self.stop()
           └─> RETURNS to ScreenManager

6. Loop back to step 4 (show menu again)

7. User selects "Exit" from menu
   └─> Callback sets manager.running = False
   └─> Callback calls self.stop() to exit menu
   └─> Menu RETURNS to ScreenManager
   └─> while self.running: exits
   └─> Cleanup and disconnect
   └─> Program ends
```

### Example: Simple Scale Return Flow

```python
# User is viewing Simple Scale screen
# SimpleScale.run() is executing: while self.running: loop()

# User presses LEFT button
# ↓
async def on_left():
    self.stop()  # Sets self.running = False
# ↓
# Next iteration of while self.running: sees False
# ↓
# Loop exits, run() method returns
# ↓
# Control returns to ScreenManager.switch_screen()
# ↓
# ScreenManager continues to next line: loop back to menu
```

### Why This Works

- **No infinite loops**: Every `while` loop has an exit condition
- **Voluntary control**: Screens decide when they're done
- **Blocking is OK**: `await screen.run()` blocks until screen is done
- **Simple flow**: Linear, easy to follow, no complex state machines
- **Predictable**: Control always returns to the same place (ScreenManager)

---

## Proposed File Structure

```
firmware/
├── screens/
│   ├── base_screen.py           [MODIFIED: Remove connection, accept hardware]
│   ├── connection_screen.py     [NEW: Handle connection phase]
│   ├── screen_manager.py        [NEW: Manage transitions]
│   ├── menu/
│   │   ├── menu_screen.py       [MODIFIED: Accept hardware in __init__]
│   │   └── menu_option.py       [NO CHANGE]
│   ├── simple_scale/
│   │   └── simple_scale.py      [MODIFIED: Accept hardware in __init__]
│   └── shot_profile/
│       └── shot_profile.py      [MODIFIED: Accept hardware in __init__]
├── main.py                      [NEW: Application entry point]
```

---

## Detailed Design

### 1. ConnectionScreen Implementation

```python
class ConnectionScreen(BaseScreen):
    """Dedicated screen for scale connection"""

    def __init__(self, display: IOController, scale: BookooScale):
        # Note: Only needs display initially, scale not yet connected
        self.display = display
        self.scale = scale

    def show_splash(self, message, color="black"):
        """Display connection status message"""
        # Same implementation as current BaseScreen.show_splash()

    async def attempt_connection(self) -> bool:
        """Single connection attempt with visual feedback"""
        self.show_splash("Connecting...", "blue")
        print("Connecting to scale...")

        connected = await self.scale.establish_connection()

        if not connected:
            print("Failed to connect to scale")
            self.show_splash("Connection\nFailed", "red")
            await asyncio.sleep(1)
        else:
            print("Connected!")
            self.show_splash("Connected!", "green")
            await asyncio.sleep(0.5)

        return connected

    async def run_until_connected(self):
        """Connect with infinite retry (non-blocking for transitions)"""
        while True:
            if await self.attempt_connection():
                return  # Success - caller can transition to next screen
```

### 2. Refactored BaseScreen

```python
class BaseScreen:
    """Abstract base class for all screens"""

    def __init__(self, scale: BookooScale, display: IOController):
        """
        Initialize screen with hardware dependencies

        Args:
            scale: Connected BookooScale instance
            display: IOController instance
        """
        self.scale = scale
        self.display = display
        self.running = False

    def stop(self):
        """Signal the screen to stop and return control voluntarily"""
        self.running = False

    def show_splash(self, message, color="black"):
        """Utility for displaying messages (moved from old BaseScreen)"""
        # Implementation stays the same

    async def setup(self):
        """Override: Setup after hardware is ready"""
        pass

    async def loop(self):
        """Override: Main screen loop"""
        raise NotImplementedError("Subclasses must implement loop()")

    async def run(self):
        """
        Run screen lifecycle until stop() is called.
        When this method returns, control goes back to ScreenManager.
        """
        await self.setup()
        self.running = True

        try:
            while self.running:
                await self.loop()
        except KeyboardInterrupt:
            print("\nShutting down...")

        # When running becomes False, loop exits and control returns
```

### 3. ScreenManager Implementation

```python
class ScreenManager:
    """Manages application flow and screen transitions"""

    def __init__(self):
        # Initialize hardware once for entire application
        self.scale = BookooScale()
        self.display = VirtualIOController()
        self.current_screen = None
        self.running = True
        self.selected_screen = None  # Track which screen was selected from menu

    async def show_connection_screen(self) -> bool:
        """Show connection screen until connected"""
        connection_screen = ConnectionScreen(self.display, self.scale)
        await connection_screen.run_until_connected()
        # When this returns, connection succeeded
        return True

    async def switch_screen(self, screen_class, *args, **kwargs):
        """
        Generic screen switcher - instantiates and runs any screen class
        Blocks until the screen voluntarily returns control.

        Args:
            screen_class: The screen class to instantiate
            *args: Additional positional arguments for screen constructor
            **kwargs: Additional keyword arguments for screen constructor
        """
        # Hardware is always first two arguments
        screen = screen_class(self.scale, self.display, *args, **kwargs)
        self.current_screen = screen

        # Run the screen - blocks until screen calls stop() and returns
        await screen.run()

        # When we get here, the screen has voluntarily returned control

    async def show_menu(self):
        """
        Show main menu and wait for selection.
        Menu callbacks should set self.selected_screen to indicate choice.
        """
        from firmware.screens.menu.menu_screen import MenuScreen
        from firmware.screens.menu.menu_option import MenuOption
        from firmware.screens.simple_scale.simple_scale import SimpleScale
        from firmware.screens.shot_profile.shot_profile import ShotProfile

        # Reset selection
        self.selected_screen = None

        # Define menu options
        # Note: Callbacks will set selected_screen, then stop the menu
        def select_simple_scale():
            self.selected_screen = SimpleScale
            self.current_screen.stop()  # Tell menu to exit

        def select_shot_profile():
            self.selected_screen = ShotProfile
            self.current_screen.stop()

        async def reconnect():
            await self.show_connection_screen()

        def exit_app():
            self.running = False
            self.current_screen.stop()

        options = [
            MenuOption("Simple Scale", callback=select_simple_scale),
            MenuOption("Shot Profile", callback=select_shot_profile),
            MenuOption("Reconnect", callback=reconnect),
            MenuOption("Exit", callback=exit_app),
        ]

        # Run menu - blocks until user makes selection
        await self.switch_screen(MenuScreen, "MAIN MENU", options)

        # When we get here, menu has returned control

    async def start(self):
        """Application entry point - main control loop"""
        # Phase 1: Connect to scale
        await self.show_connection_screen()

        # Phase 2: Main application loop
        while self.running:
            # Show menu and wait for selection
            await self.show_menu()

            # If user selected a screen (not exit), run it
            if self.selected_screen:
                await self.switch_screen(self.selected_screen)
                # When screen returns, loop back to menu

        # Cleanup when exiting
        print("Exiting application...")
        await self.scale.disconnect()
```

### 4. Updated Screen Classes

All screen classes need minimal changes:

```python
# simple_scale.py
class SimpleScale(BaseScreen):
    def __init__(self, scale: BookooScale, display: IOController):
        super().__init__(scale, display)  # Pass to parent
        self.weight_font = None
        self.hint_font = None
        self.timer_running = False

    async def setup(self):
        """Initialize fonts and button callbacks"""
        # ... existing font loading code ...

        loop = asyncio.get_event_loop()

        # Button A: Start/Stop Timer
        async def on_button_a():
            # ... existing timer logic ...

        # Button B: Tare
        async def on_button_b():
            # ... existing tare logic ...

        # LEFT Button: Return to menu (NEW!)
        async def on_left():
            self.stop()  # Signal to exit and return control

        self.display.on_a = lambda: asyncio.run_coroutine_threadsafe(on_button_a(), loop)
        self.display.on_b = lambda: asyncio.run_coroutine_threadsafe(on_button_b(), loop)
        self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(on_left(), loop)

    # loop() remains unchanged
```

```python
# shot_profile.py
class ShotProfile(BaseScreen):
    def __init__(self, scale: BookooScale, display: IOController):
        super().__init__(scale, display)  # Pass to parent
        # ... rest of initialization

    async def setup(self):
        """Initialize after connection"""
        # ... existing font loading code ...

        loop = asyncio.get_event_loop()

        # Button A: Start/Stop Timer
        async def on_button_a():
            # ... existing recording logic ...

        # Button B: Reset Timer
        async def on_button_b():
            # ... existing reset logic ...

        # LEFT Button: Return to menu (NEW!)
        async def on_left():
            self.stop()  # Signal to exit and return control

        self.display.on_a = lambda: asyncio.run_coroutine_threadsafe(on_button_a(), loop)
        self.display.on_b = lambda: asyncio.run_coroutine_threadsafe(on_button_b(), loop)
        self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(on_left(), loop)

    # loop() remains unchanged
```

```python
# menu_screen.py
class MenuScreen(BaseScreen):
    def __init__(self, scale: BookooScale, display: IOController,
                 title: str, options: list[MenuOption], ...):
        super().__init__(scale, display)  # Pass to parent
        self.title = title
        self.options = options
        # ... rest of initialization

    async def setup(self):
        """Configure button handlers for up/down navigation"""
        # ... existing font loading code ...

        loop = asyncio.get_event_loop()

        async def on_up():
            self.move_up()

        async def on_down():
            self.move_down()

        async def on_select():
            """Handle selection of current menu option"""
            if self.options and 0 <= self.current_index < len(self.options):
                selected_option = self.options[self.current_index]
                print(f"[MENU] Selected: {selected_option.label}")
                # Execute the callback - callback is responsible for calling stop()
                await selected_option.execute()

        self.display.on_up = lambda: asyncio.run_coroutine_threadsafe(on_up(), loop)
        self.display.on_down = lambda: asyncio.run_coroutine_threadsafe(on_down(), loop)
        self.display.on_center = lambda: asyncio.run_coroutine_threadsafe(on_select(), loop)

    # loop() remains unchanged
```

### 5. New main.py Entry Point

```python
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from firmware.screens.screen_manager import ScreenManager


async def main():
    """Application entry point"""
    manager = ScreenManager()
    await manager.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
```

---

## Migration Strategy

### Phase 1: Create New Components
1. Create `connection_screen.py`
2. Create `screen_manager.py`
3. Create `main.py`

### Phase 2: Update BaseScreen
1. Remove hardware initialization from `BaseScreen.__init__()`
2. Remove `connect_to_scale()` method
3. Update `run()` to not create hardware or connect
4. Add hardware parameters to `__init__()`
5. Keep `show_splash()` utility method

### Phase 3: Update All Screen Classes
1. Update `SimpleScale.__init__()` to accept hardware
2. Update `ShotProfile.__init__()` to accept hardware
3. Update `MenuScreen.__init__()` to accept hardware
4. Remove hardware initialization from each class

### Phase 4: Update Standalone Entry Points (Optional)
Keep standalone entry points for testing individual screens:

```python
# simple_scale.py
if __name__ == "__main__":
    async def main():
        scale = BookooScale()
        display = VirtualIOController()

        # Connection phase
        connection_screen = ConnectionScreen(display, scale)
        await connection_screen.run_until_connected()

        # Run screen
        app = SimpleScale(scale, display)
        await app.run()

    asyncio.run(main())
```

### Phase 5: Test & Validate
1. Test `main.py` → Connection → Menu flow
2. Test menu options launching other screens
3. Test standalone screen entry points
4. Test connection failure/retry behavior

---

## Benefits of This Approach

### 1. **Single Connection Phase**
- Connect once at startup
- All screens share the same connection
- No redundant connection attempts

### 2. **Clear Separation of Concerns**
- `ConnectionScreen`: Handles connection logic
- `BaseScreen`: Provides screen lifecycle framework
- `ScreenManager`: Orchestrates application flow
- Individual screens: Focus on their specific functionality

### 3. **Elegant Screen Transitions**
- Single reusable `switch_screen()` method handles all screen changes
- Can navigate from menu to screens and back
- Hardware persists across transitions
- No disconnection/reconnection overhead
- Easy to add new screens to menu (just add MenuOption with lambda)

### 4. **Improved Testability**
- Can mock hardware and inject into screens
- Can test screens without connection logic
- Can test connection logic in isolation

### 5. **Better User Experience**
- Single connection splash at startup
- Smooth transitions between screens
- Visual feedback during connection (via ConnectionScreen)
- Option to reconnect from menu if needed

### 6. **Maintainability & Extensibility**
- Connection logic in one place
- Hardware lifecycle clearly managed
- Each screen's responsibility is clear
- Adding new screens requires only:
  1. Create screen class inheriting from BaseScreen
  2. Add MenuOption with `callback=lambda: self.switch_screen(NewScreen)`
- Generic `switch_screen()` eliminates boilerplate
- No need to write separate launch methods for each screen

---

## Open Questions / Considerations

### 1. Screen Transitions with Cleanup
**Question**: How do we stop a screen's loop when transitioning to another?

**Options**:
- A) Add `stop()` method to BaseScreen, set a flag to break loop
- B) Use asyncio tasks and cancel them
- C) Restructure loop to check a "running" flag

**Recommendation**: Option A (simplest, most explicit)

```python
class BaseScreen:
    def __init__(self, scale, display):
        self.scale = scale
        self.display = display
        self.running = False

    async def run(self):
        await self.setup()
        self.running = True
        try:
            while self.running:
                await self.loop()
        except KeyboardInterrupt:
            print("\nShutting down...")

    def stop(self):
        self.running = False
```

### 2. Menu Integration
**Question**: How do menu callbacks launch other screens and return to menu?

**Options**:
- A) Menu callbacks return screen class, ScreenManager handles transition
- B) Menu callbacks directly launch screens (blocks menu until screen exits)
- C) Use a message/event system

**Recommendation**: Option B initially (simpler), Option A for better UX

With Option B:
- User selects "Simple Scale" → Simple scale runs
- User exits (new button?) → Returns to menu
- Keeps code simple, linear flow

### 3. Connection Loss Handling
**Question**: What happens if scale disconnects while using a screen?

**Options**:
- A) Screens detect and show error, return to menu
- B) Automatic reconnection in background
- C) Return to ConnectionScreen automatically

**Recommendation**: Start with Option A (explicit), add Option C later

### 4. Backward Compatibility
**Question**: Should standalone screen entry points still work?

**Recommendation**: YES - keep them for development/testing

Each screen's `if __name__ == "__main__"` should:
1. Create hardware
2. Run ConnectionScreen
3. Run the screen

---

## Example Usage After Refactor

### Starting the Application
```bash
python main.py
```

**Flow**:
1. Shows "Connecting..." splash
2. Connects to scale (retries on failure)
3. Shows "Connected!" splash
4. Transitions to main menu
5. User selects screen from menu
6. Screen runs with already-connected hardware

### Testing a Single Screen
```bash
python firmware/screens/simple_scale/simple_scale.py
```

**Flow** (same as before, for compatibility):
1. Shows "Connecting..." splash
2. Connects to scale
3. Shows "Connected!" splash
4. Runs simple scale screen

### Adding a New Screen (Extensibility Example)

**Step 1**: Create your screen class
```python
# firmware/screens/calibration/calibration_screen.py
class CalibrationScreen(BaseScreen):
    def __init__(self, scale, display):
        super().__init__(scale, display)

    async def setup(self):
        # Your setup logic
        pass

    async def loop(self):
        # Your screen logic
        await asyncio.sleep(0.1)
```

**Step 2**: Add one line to the menu
```python
# In ScreenManager.show_menu()
MenuOption("Calibration",
          callback=lambda: self.switch_screen(CalibrationScreen)),
```

**That's it!** The `switch_screen()` method handles:
- Instantiating the screen with hardware
- Running the screen
- Managing the transition

No need to write separate `launch_calibration()` methods or duplicate boilerplate code.

---

## Test Plan

> **⚠️ IMPORTANT**: This test plan is for **HUMAN REVIEW ONLY** after the refactor is complete.
>
> **DO NOT** implement automated tests or run these tests as part of the refactor implementation.
>
> This is a manual verification checklist for the developer to validate the completed refactor.

### 1. Connection Screen Tests

**Test 1.1: Successful Connection**
- [ ] Run `python main.py`
- [ ] Verify "Connecting..." splash appears (blue text)
- [ ] Verify scale connects successfully
- [ ] Verify "Connected!" splash appears (green text)
- [ ] Verify automatic transition to menu screen

**Test 1.2: Connection Retry on Failure**
- [ ] Turn off scale or move out of Bluetooth range
- [ ] Run `python main.py`
- [ ] Verify "Connecting..." splash appears
- [ ] Verify "Connection\nFailed" splash appears (red text)
- [ ] Verify retry attempt after 1 second delay
- [ ] Turn on scale and verify connection succeeds
- [ ] Verify transition to menu after successful connection

**Test 1.3: Reconnect from Menu**
- [ ] Launch application (already connected)
- [ ] From main menu, select "Reconnect" option
- [ ] Verify connection screen runs again
- [ ] Verify return to menu after connection

### 2. Main Menu Tests

**Test 2.1: Menu Display**
- [ ] After connection, verify menu displays:
  - [ ] Header: "MAIN MENU"
  - [ ] Options: "Simple Scale", "Shot Profile", "Reconnect", "Exit"
  - [ ] Footer: Page indicator
- [ ] Verify first option is highlighted (black background, white text)

**Test 2.2: Menu Navigation**
- [ ] Press UP button → verify highlight moves up (stops at top)
- [ ] Press DOWN button → verify highlight moves down
- [ ] Navigate through all menu options
- [ ] Verify page indicator updates if menu spans multiple pages

**Test 2.3: Menu Selection**
- [ ] Highlight "Simple Scale" and press CENTER button
- [ ] Verify Simple Scale screen launches
- [ ] (Test screen exit mechanism when implemented)

### 3. Screen Switching Tests

**Test 3.1: Launch Simple Scale**
- [ ] From menu, select "Simple Scale"
- [ ] Verify SimpleScale screen displays:
  - [ ] Weight reading in center (large font)
  - [ ] Button hints at bottom
- [ ] Press A button → verify timer starts/stops
- [ ] Press B button → verify scale tares
- [ ] Verify no connection splash appears (already connected)

**Test 3.2: Launch Shot Profile**
- [ ] From menu, select "Shot Profile"
- [ ] Verify ShotProfile screen displays:
  - [ ] Graph area with axes
  - [ ] Info section with timer and weight
- [ ] Press A button → verify recording starts
- [ ] Verify graph updates in real-time
- [ ] Press B button → verify reset works
- [ ] Verify no connection splash appears (already connected)

**Test 3.3: Multiple Screen Transitions**
- [ ] Launch Simple Scale → verify it works
- [ ] Return to menu (when exit implemented)
- [ ] Launch Shot Profile → verify it works
- [ ] Verify scale connection persists throughout transitions
- [ ] Check for memory leaks (monitor system resources)

### 4. Standalone Screen Tests

**Test 4.1: Standalone Simple Scale**
- [ ] Run `python firmware/screens/simple_scale/simple_scale.py`
- [ ] Verify connection splash appears
- [ ] Verify scale connects
- [ ] Verify Simple Scale screen functions normally
- [ ] Verify behavior matches pre-refactor implementation

**Test 4.2: Standalone Shot Profile**
- [ ] Run `python firmware/screens/shot_profile/shot_profile.py`
- [ ] Verify connection splash appears
- [ ] Verify scale connects
- [ ] Verify Shot Profile screen functions normally
- [ ] Verify behavior matches pre-refactor implementation

**Test 4.3: Standalone Menu**
- [ ] Run `python pocs/menu_poc.py` (if updated)
- [ ] Verify it still works or has been properly deprecated

### 5. Exit and Cleanup Tests

**Test 5.1: Exit from Menu**
- [ ] Launch application
- [ ] Navigate to "Exit" option in menu
- [ ] Press CENTER button
- [ ] Verify application exits cleanly
- [ ] Verify "Exiting application..." message in console
- [ ] Verify scale disconnects (check console logs)
- [ ] Verify no error messages or exceptions

**Test 5.2: Keyboard Interrupt**
- [ ] Launch application
- [ ] Press Ctrl+C at various stages:
  - [ ] During connection screen
  - [ ] On menu screen
  - [ ] On Simple Scale screen
  - [ ] On Shot Profile screen
- [ ] Verify graceful shutdown in each case
- [ ] Verify scale disconnects properly

### 6. Hardware Lifecycle Tests

**Test 6.1: Single Hardware Instance**
- [ ] Add debug print statements to `BookooScale.__init__()` and `VirtualIOController.__init__()`
- [ ] Run `python main.py`
- [ ] Launch multiple screens from menu
- [ ] Verify hardware constructors are called only ONCE
- [ ] Remove debug statements

**Test 6.2: Hardware Sharing**
- [ ] Run application and launch Simple Scale
- [ ] Tare the scale (sets scale state)
- [ ] Return to menu
- [ ] Launch Shot Profile
- [ ] Verify scale state persists (not re-initialized)
- [ ] Verify weight reading continues from tared position

**Test 6.3: Connection Persistence**
- [ ] Run application and connect to scale
- [ ] Navigate through multiple screens
- [ ] Verify connection remains active throughout
- [ ] Check console logs for unexpected disconnection/reconnection messages

### 7. Virtual Display Tests

**Test 7.1: Display Accessibility**
- [ ] Launch application
- [ ] Open browser to http://localhost:5000/display
- [ ] Verify connection screen appears
- [ ] Verify menu appears after connection
- [ ] Launch each screen and verify display updates in browser

**Test 7.2: Button Functionality via Web UI**
- [ ] On menu screen, click virtual buttons (UP, DOWN, CENTER)
- [ ] Verify menu responds correctly
- [ ] Launch Simple Scale
- [ ] Click virtual A and B buttons
- [ ] Verify timer and tare functions work

### 8. Error Handling Tests

**Test 8.1: Scale Disconnection During Use**
- [ ] Connect and launch Simple Scale
- [ ] Turn off scale or move out of range
- [ ] Observe behavior (current implementation may not handle this)
- [ ] Document behavior for future enhancement

**Test 8.2: Invalid Menu Selections**
- [ ] Modify menu to include option with no callback
- [ ] Select that option
- [ ] Verify no crash occurs (graceful handling)

### 9. Regression Tests

**Test 9.1: Scale Communication**
- [ ] Verify all scale commands still work:
  - [ ] `send_tare()` → scale zeros
  - [ ] `send_timer_start()` → timer starts
  - [ ] `send_timer_stop()` → timer stops
  - [ ] `send_timer_reset()` → timer resets
  - [ ] `read_weight()` → returns current weight
  - [ ] `read_time()` → returns timer value

**Test 9.2: Display Rendering**
- [ ] Verify all screens render correctly at 240x240 resolution
- [ ] Verify fonts load properly (with fallbacks)
- [ ] Verify colors display correctly
- [ ] Verify no visual regressions compared to pre-refactor

**Test 9.3: Performance**
- [ ] Verify Simple Scale updates at ~10Hz
- [ ] Verify Shot Profile updates at ~10Hz during recording
- [ ] Verify Menu updates at ~20Hz
- [ ] Compare performance to pre-refactor implementation

### 10. Code Quality Validation

**Test 10.1: Import Structure**
- [ ] Verify no circular import errors
- [ ] Run `python -m py_compile` on all modified files
- [ ] Verify all files compile without syntax errors

**Test 10.2: Architecture Validation**
- [ ] Review `base_screen.py` → verify no connection logic remains
- [ ] Review `connection_screen.py` → verify it handles connection only
- [ ] Review `screen_manager.py` → verify clean separation of concerns
- [ ] Review all screen classes → verify they accept hardware in `__init__()`

**Test 10.3: Documentation**
- [ ] Verify docstrings are present for all new classes and methods
- [ ] Verify CLAUDE.md is updated with new architecture
- [ ] Verify README has updated commands if needed

---

## Summary

This refactor achieves:

✅ **Separation of connection logic** into dedicated `ConnectionScreen`
✅ **Shared hardware** across all screens via dependency injection
✅ **Clear application flow** managed by `ScreenManager`
✅ **Single entry point** (`main.py`) with connection → menu → screens
✅ **Generic screen switching** via single reusable `switch_screen()` method
✅ **Visual feedback** centralized in ConnectionScreen (no duplication)
✅ **Maintains abstraction** - screens don't know about connection details
✅ **Better encapsulation** - each component has single responsibility
✅ **Preserves standalone testing** - can still run screens individually
✅ **Easy extensibility** - adding new screens requires minimal code

The architecture is now ready for screen transitions, hardware sharing, and more complex application flows while maintaining clean separation of concerns.
