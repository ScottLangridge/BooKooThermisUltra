# Settings & Colorscheme System - Implementation Plan

## Overview
Implementing a comprehensive settings system with colorscheme support. This is a foundation feature that will support future settings beyond just colorschemes.

## Design Decisions & Rationale

### File Structure
```
config/
├── default_settings.json    # Tracked in git, defines schema + defaults
├── settings.json             # User overrides only (can be gitignored by user)
└── colorschemes.json         # Available colorscheme definitions
```

**Rationale:**
- Two-file approach allows shipping default updates without touching user preferences
- Settings merging pattern: load defaults, overlay user settings
- Colorschemes separate because they're not user settings, they're available options

### Settings.json Structure
```json
{
  "colorscheme": "Dark"
}
```

**Default_settings.json Structure:**
```json
{
  "colorscheme": "Dark"
}
```

**Rationale:**
- User file only contains values that differ from defaults
- Simple flat structure for now (can nest later if needed)
- If user file is empty/missing, falls back to defaults

### Colorschemes.json Structure
```json
{
  "Dark": {
    "background": "#1e1e1e",
    "foreground": "#ffffff",
    "primary_accent": "#007acc",
    "secondary_accent": "#4ec9b0",
    "tertiary_accent": "#ce9178",
    "success": "#4ec9b0",
    "error": "#f48771",
    "info": "#007acc"
  },
  "Light": {
    "background": "#ffffff",
    "foreground": "#000000",
    ...
  }
}
```

**Rationale:**
- Hex colors for precision and web compatibility
- Named colorschemes as top-level keys for easy lookup
- All colorschemes have identical schema (enforced by ColorScheme class)

### Colorscheme Palette Design

Need 5+ visually appealing colorschemes. Considerations:
- High contrast for readability on 240x240 display
- Distinct accent colors that work together
- Professional appearance
- Cover different use cases (dark mode, light mode, themed)

**Planned colorschemes:**
1. **Dark** - Classic dark theme (VS Code Dark+ inspired)
2. **Light** - Clean light theme (high contrast)
3. **Espresso** - Warm browns/creams (coffee theme, fits the app!)
4. **Ocean** - Cool blues/teals (calming)
5. **Sunset** - Warm oranges/purples (vibrant)
6. **Forest** - Greens/earth tones (natural)

### Class Architecture

#### SettingsManager
**Responsibilities:**
- Load and merge default_settings.json + settings.json
- Provide read access to settings
- Provide write access with auto-save or explicit save
- Handle missing files gracefully
- Singleton pattern for global access

**Interface:**
```python
class SettingsManager:
    _instance = None  # Singleton

    @classmethod
    def get_instance(cls) -> 'SettingsManager':
        """Get singleton instance"""

    def __init__(self):
        """Load settings on first instantiation"""

    def get(self, key: str, default=None):
        """Get setting value (merged from defaults + user)"""

    def set(self, key: str, value):
        """Set setting value (in-memory, call save() to persist)"""

    def save(self):
        """Write current settings to settings.json"""

    def get_colorscheme(self) -> 'ColorScheme':
        """Get current colorscheme object"""

    def get_available_colorschemes(self) -> list[str]:
        """Get list of available colorscheme names"""
```

**File Handling:**
- If default_settings.json missing: Create with sensible defaults
- If settings.json missing: Create empty {} (all defaults used)
- If colorschemes.json missing: Create with builtin colorschemes

#### ColorScheme
**Responsibilities:**
- Represent a single colorscheme
- Provide named access to colors
- Load from colorschemes.json by name

**Interface:**
```python
class ColorScheme:
    def __init__(self, name: str, colors: dict):
        """Initialize from colorscheme data"""
        self.name = name
        self.background = colors['background']
        self.foreground = colors['foreground']
        self.primary_accent = colors['primary_accent']
        self.secondary_accent = colors['secondary_accent']
        self.tertiary_accent = colors['tertiary_accent']
        self.success = colors['success']
        self.error = colors['error']
        self.info = colors['info']

    @staticmethod
    def load_all() -> dict[str, 'ColorScheme']:
        """Load all colorschemes from colorschemes.json"""

    @staticmethod
    def load(name: str) -> 'ColorScheme':
        """Load specific colorscheme by name"""
```

### Global Access Pattern

**Question:** How do screens access the current colorscheme?

**Options:**
1. Via SettingsManager directly: `SettingsManager.get_instance().get_colorscheme()`
2. Via BaseScreen property: `self.colorscheme`
3. Module-level singleton: `from settings import current_colorscheme`

**Decision:** Option 2 (via BaseScreen)
**Rationale:**
- BaseScreen is already the common ancestor of all screens
- Natural place for shared functionality
- Easy to access: `self.colorscheme.background`
- SettingsManager remains internal implementation detail

**Implementation:**
```python
class BaseScreen:
    def __init__(self, scale, display):
        self.scale = scale
        self.display = display
        self.running = False
        self._settings_manager = SettingsManager.get_instance()
        self.colorscheme = self._settings_manager.get_colorscheme()

    def refresh_colorscheme(self):
        """Reload colorscheme (called when settings change)"""
        self.colorscheme = self._settings_manager.get_colorscheme()
```

### Color Mapping Strategy

Current hardcoded colors → colorscheme slots:

**SimpleScale:**
- Background: white → `colorscheme.background`
- Weight text: black → `colorscheme.foreground`
- Hint text: gray → `colorscheme.foreground` (or 50% opacity?)
- Error text (no reading): red → `colorscheme.error`

**ShotProfile:**
- Background: white → `colorscheme.background`
- Text: black → `colorscheme.foreground`
- Borders/axes: black → `colorscheme.foreground`
- Weight graph line: blue → `colorscheme.secondary_accent`
- Flowrate graph line: red → `colorscheme.tertiary_accent`
- Axis labels: black → `colorscheme.foreground`

**MenuScreen:**
- Background (normal): white → `colorscheme.background`
- Text (normal): black → `colorscheme.foreground`
- Background (highlighted): black → `colorscheme.primary_accent`
- Text (highlighted): white → `colorscheme.background` (inverted)

**ConnectionScreen:**
- Background: white → `colorscheme.background`
- "Connecting..." text: blue → `colorscheme.info`
- "Connected!" text: green → `colorscheme.success`
- "Connection Failed" text: red → `colorscheme.error`

**BaseScreen.show_splash:**
- Background: white → `colorscheme.background`
- Text: color parameter → keep flexible, default to `colorscheme.foreground`

**Issues to solve:**
- Gray color in SimpleScale: Could use foreground with transparency, or add a `secondary_foreground` slot
- Menu highlight inversion: Works well with background/primary_accent

**Decision:** Keep it simple for now. For gray, we can:
- Option 1: Use foreground color (will be readable)
- Option 2: Add `muted` color slot to colorscheme
- Going with Option 1 initially, can add muted later if needed

### Menu Structure Implementation

**Three-tier structure:**
```
Main Menu (MenuScreen)
└─ Settings (callback)
   └─ Settings Menu (MenuScreen)
      └─ Colourscheme (callback)
         └─ Colourscheme Picker (ColorschemePickerScreen)
```

**Navigation pattern:**
- Main Menu: User presses RIGHT/CENTER on "Settings"
  - Callback launches Settings Menu via ScreenManager.switch_screen()
- Settings Menu: User presses RIGHT/CENTER on "Colourscheme"
  - Callback launches Colourscheme Picker via ScreenManager.switch_screen()
- Colourscheme Picker: User presses LEFT
  - Saves settings, returns to Settings Menu

**Implementation approach:**
Use existing ScreenManager.switch_screen() pattern. Each submenu is a screen that runs until stop() is called.

**Callback pattern for Main Menu:**
```python
def open_settings():
    # Can't use switch_screen directly from here
    # Need to stop current menu and signal to run settings
    self.selected_screen = SettingsMenu
    self.current_screen.stop()
```

**Wait, issue:** SettingsMenu isn't a simple screen, it's another menu that needs callbacks...

**Better approach:** Create a dedicated method in ScreenManager for the settings flow

Actually, let's think about this more carefully...

**Current pattern:**
- Main menu shows options
- User selects option
- Callback sets selected_screen and calls stop()
- ScreenManager sees selected_screen and runs it
- When that screen stops, returns to menu

**For nested menus:**
Option 1: Each submenu is a screen, ScreenManager doesn't know about nesting
Option 2: ScreenManager has special handling for nested menus
Option 3: Create a SettingsScreen that internally manages its own submenu navigation

**Decision: Option 1** - Keep it simple, use existing pattern
- Settings Menu is just another screen (happens to be a MenuScreen)
- Colourscheme Picker is just another screen
- Each one knows how to launch the next level or return to previous

**Implementation:**
```python
# In ScreenManager.show_menu():
def open_settings_menu():
    self.selected_screen = lambda scale, display: create_settings_menu(scale, display, self)
    self.current_screen.stop()

# Helper function:
def create_settings_menu(scale, display, manager):
    def open_colorscheme_picker():
        manager.selected_screen = ColorschemePickerScreen
        manager.current_screen.stop()

    options = [
        MenuOption("Colourscheme", callback=open_colorscheme_picker),
        # Future settings here
    ]
    return MenuScreen(scale, display, "SETTINGS", options)
```

Hmm, this is getting messy with closures. Let me rethink...

**Better approach:**
Create dedicated screen classes for Settings flow:
- `SettingsMenuScreen` - Wraps MenuScreen with settings-specific options
- `ColorschemePickerScreen` - Custom screen for picking colorschemes

The callbacks can reference the manager because screens receive it... wait, no they don't. They receive scale and display.

**Actually, looking at current code:**
In ScreenManager.show_menu(), callbacks reference `self` (the manager) and `self.current_screen`. This works because show_menu() is a method of ScreenManager.

So for Settings Menu, we need similar access to manager. How?

**Solution:** Pass manager to Settings Menu screen via constructor
```python
class SettingsMenuScreen(BaseScreen):
    def __init__(self, scale, display, manager):
        super().__init__(scale, display)
        self.manager = manager
```

Then in ScreenManager:
```python
def open_settings_menu():
    self.selected_screen = ('SettingsMenuScreen', {'manager': self})
    self.current_screen.stop()
```

Wait, but switch_screen expects a class and args...
```python
await self.switch_screen(selected_screen)
```

Let me check the actual implementation:
```python
async def switch_screen(self, screen_class, *args, **kwargs):
    screen = screen_class(self.scale, self.display, *args, **kwargs)
    ...
```

So I can do:
```python
self.selected_screen = SettingsMenuScreen
self.selected_screen_args = (self,)  # Pass manager as extra arg
```

But that requires modifying ScreenManager to handle selected_screen_args...

**Simpler solution:** Create the Settings Menu in ScreenManager as a method, similar to show_menu():
```python
async def show_settings_menu(self):
    """Show settings submenu"""
    self.selected_screen = None

    def open_colorscheme_picker():
        self.selected_screen = ColorschemePickerScreen
        self.current_screen.stop()

    options = [
        MenuOption("Colourscheme", callback=open_colorscheme_picker),
    ]

    await self.switch_screen(MenuScreen, "SETTINGS", options)
```

Then in main menu:
```python
async def open_settings():
    # Need to stop current menu, then show settings menu
    # But we can't call async from callback...
    pass
```

This is tricky because callbacks can't be async in the menu (well, they can via MenuOption.execute, but we need to stop the current menu AND launch the next one).

**Rethinking the whole approach:**

The issue is that MenuOption callbacks execute, then the menu keeps running. We need to stop the current menu and launch a new one.

Current pattern for launching screens:
```python
def select_simple_scale():
    self.selected_screen = SimpleScale
    self.current_screen.stop()
```

This works because ScreenManager checks selected_screen after the menu stops.

For nested menus, we need the same pattern:
```python
def select_settings():
    self.selected_screen = SettingsMenuScreen  # Or a factory function
    self.current_screen.stop()
```

Then in ScreenManager.start(), after showing a menu:
```python
if self.selected_screen:
    if self.selected_screen == SettingsMenuScreen:
        await self.show_settings_menu()
    else:
        await self.switch_screen(self.selected_screen)
```

But this is messy - special casing menus.

**Even better approach:**
Make SettingsMenuScreen a proper screen class that creates its own menu internally:

```python
class SettingsMenuScreen(BaseScreen):
    def __init__(self, scale, display, parent_manager):
        super().__init__(scale, display)
        self.parent_manager = parent_manager

    async def setup(self):
        # We'll create and manage a MenuScreen internally
        pass

    async def loop(self):
        # Actually, this won't work because we need to run the menu screen
        pass
```

This is getting complicated. Let me look at how the current menu works...

**Current menu flow:**
1. ScreenManager.show_menu() creates MenuScreen and calls switch_screen()
2. switch_screen() instantiates the menu and calls menu.run()
3. menu.run() runs the menu loop until stop() is called
4. Callback sets selected_screen and calls stop()
5. Control returns to ScreenManager.start()
6. ScreenManager checks selected_screen and runs it

**For nested menus, I can use the SAME pattern:**
1. Main menu callback sets selected_screen to a **factory function** that creates the settings menu
2. ScreenManager.start() calls the factory to get the screen instance

Wait, selected_screen is supposed to be a class, not an instance...

Let me check the actual code:
```python
if self.selected_screen:
    await self.switch_screen(self.selected_screen)
```

And switch_screen:
```python
async def switch_screen(self, screen_class, *args, **kwargs):
    screen = screen_class(self.scale, self.display, *args, **kwargs)
```

So it expects a class. But I need to pass additional args...

**Aha! I can use a wrapper/factory class:**
```python
class SettingsMenuFactory:
    def __init__(self, manager):
        self.manager = manager

    def __call__(self, scale, display):
        # Return a configured MenuScreen
        def open_colorscheme_picker():
            self.manager.selected_screen = ColorschemePickerScreen
            self.manager.current_screen.stop()

        options = [
            MenuOption("Colourscheme", callback=open_colorscheme_picker),
        ]

        return MenuScreen(scale, display, "SETTINGS", options)
```

Then:
```python
def open_settings():
    self.selected_screen = SettingsMenuFactory(self)
    self.current_screen.stop()
```

And in switch_screen:
```python
screen = screen_class(self.scale, self.display, *args, **kwargs)
```

This will call `SettingsMenuFactory().__call__(scale, display)`, which returns a MenuScreen!

**Wait, but switch_screen does:**
```python
screen = screen_class(self.scale, self.display)
```

It's calling screen_class as a constructor, not as a callable. So if screen_class is an instance of SettingsMenuFactory, it will try to instantiate it again...

Let me re-read switch_screen:
```python
async def switch_screen(self, screen_class, *args, **kwargs):
    screen = screen_class(self.scale, self.display, *args, **kwargs)
    self.current_screen = screen
    await screen.run()
```

So screen_class can be anything callable that takes (scale, display, *args, **kwargs) and returns a screen object.

**Perfect!** So I can do:
```python
def create_settings_menu(manager):
    """Factory function that returns a function that creates a settings menu screen"""
    def factory(scale, display):
        def open_colorscheme_picker():
            manager.selected_screen = ColorschemePickerScreen
            manager.current_screen.stop()

        options = [MenuOption("Colourscheme", callback=open_colorscheme_picker)]
        return MenuScreen(scale, display, "SETTINGS", options)

    return factory

# In main menu callback:
def open_settings():
    self.selected_screen = create_settings_menu(self)
    self.current_screen.stop()
```

This is clean! The factory closure captures the manager reference.

Actually, even simpler - use a lambda:
```python
def open_settings():
    def settings_menu_factory(scale, display):
        def open_colorscheme_picker():
            self.selected_screen = ColorschemePickerScreen
            self.current_screen.stop()

        options = [MenuOption("Colourscheme", callback=open_colorscheme_picker)]
        return MenuScreen(scale, display, "SETTINGS", options)

    self.selected_screen = settings_menu_factory
    self.current_screen.stop()
```

Perfect! This uses the existing switch_screen mechanism without modification.

### ColorschemePickerScreen Design

**Requirements:**
- Show list of available colorschemes
- Navigate with UP/DOWN
- Update entire UI in real-time as user navigates
- Save to settings.json when user exits (LEFT)
- Include a preview graph showing the accent colors

**Layout (240x240):**
```
┌─────────────────────────────┐
│     CHOOSE COLOURSCHEME     │ ← Header (40px)
├─────────────────────────────┤
│  ┌──────────────────────┐  │ ← Preview graph (120px)
│  │   Sample Graph       │  │
│  │                      │  │
│  └──────────────────────┘  │
├─────────────────────────────┤
│  > Dark                     │ ← Colorscheme list
│    Light                    │   (scrollable, highlighted)
│    Espresso                 │   (80px - about 3-4 items)
│    Ocean                    │
├─────────────────────────────┤
│   Page 1/2                  │ ← Footer if needed
└─────────────────────────────┘
```

**Alternative: Simpler layout without list, just graph with name:**
```
┌─────────────────────────────┐
│     CHOOSE COLOURSCHEME     │ ← Header (40px)
├─────────────────────────────┤
│                             │
│      ◄  Dark  ►             │ ← Current colorscheme name (centered, arrows)
│                             │
├─────────────────────────────┤
│  ┌──────────────────────┐  │ ← Preview graph (140px)
│  │                      │  │
│  │   Sample Graph       │  │
│  │                      │  │
│  └──────────────────────┘  │
├─────────────────────────────┤
│   UP/DOWN: Change           │ ← Hints (60px)
│   LEFT: Back                │
└─────────────────────────────┘
```

**Decision:** Go with the list layout - more intuitive, consistent with menu pattern

**Preview graph design:**
- Mini shot profile graph with fake data
- Weight line using secondary_accent
- Flowrate line using tertiary_accent
- Axes/border using foreground
- Background uses background color (obviously)
- Shows all accent colors in action

**Implementation approach:**
```python
class ColorschemePickerScreen(BaseScreen):
    def __init__(self, scale, display):
        super().__init__(scale, display)
        self.settings_manager = SettingsManager.get_instance()
        self.available_colorschemes = self.settings_manager.get_available_colorschemes()
        self.current_index = 0
        self.original_colorscheme = self.settings_manager.get('colorscheme')

    async def setup(self):
        # Set initial colorscheme to current selection
        current_name = self.settings_manager.get('colorscheme')
        self.current_index = self.available_colorschemes.index(current_name)

        loop = asyncio.get_event_loop()

        async def on_up():
            self.current_index = (self.current_index - 1) % len(self.available_colorschemes)
            self.update_colorscheme()

        async def on_down():
            self.current_index = (self.current_index + 1) % len(self.available_colorschemes)
            self.update_colorscheme()

        async def on_left():
            # Save and exit
            self.settings_manager.save()
            self.stop()

        self.display.on_up = lambda: asyncio.run_coroutine_threadsafe(on_up(), loop)
        self.display.on_down = lambda: asyncio.run_coroutine_threadsafe(on_down(), loop)
        self.display.on_left = lambda: asyncio.run_coroutine_threadsafe(on_left(), loop)

    def update_colorscheme(self):
        """Update current colorscheme selection (in-memory, not saved yet)"""
        selected_name = self.available_colorschemes[self.current_index]
        self.settings_manager.set('colorscheme', selected_name)
        self.refresh_colorscheme()
        # Note: This updates current screen's colorscheme, but we need to update ALL screens
        # How to do this?

    async def loop(self):
        # Draw screen with list and preview
        pass
```

**Issue: Live UI update across all screens**

When colorscheme changes in the picker, we need the entire app UI to update. But other screens aren't running - only the picker is.

**Ah wait**, the user said "the entire UI gets updated in real time" - they mean the current screen (the picker itself) updates to show the new colors. The other screens (menu, etc.) aren't visible, so they don't need to update until they're shown again.

When the picker stops and control returns to the menu, the menu will redraw with the new colorscheme because it reads colorscheme in its loop().

**So the implementation is:**
- Picker updates its own colorscheme reference when user navigates
- Picker redraws with new colors
- When picker exits, menu (and other screens) will naturally use new colorscheme on next draw

**But wait:** The picker is showing a preview graph. That graph needs to update colors. So the picker needs to refresh its colorscheme reference.

**Solution:**
```python
def update_colorscheme(self):
    selected_name = self.available_colorschemes[self.current_index]
    self.settings_manager.set('colorscheme', selected_name)
    self.refresh_colorscheme()  # Updates self.colorscheme
```

Now the picker's loop() will use the updated self.colorscheme for drawing.

Perfect!

## Implementation Order

To minimize errors and enable testing at each step:

### Phase 1: Foundation (Settings System)
1. Create `config/` directory structure
2. Create `config/colorschemes.json` with all colorscheme definitions
3. Create `config/default_settings.json`
4. Create empty `config/settings.json`
5. Implement `ColorScheme` class
6. Implement `SettingsManager` class
7. Add colorscheme property to `BaseScreen`
8. Test: Can load colorschemes, can access via BaseScreen

### Phase 2: Refactor Existing Screens
9. Refactor `BaseScreen.show_splash()` to use colorscheme
10. Refactor `ConnectionScreen` to use colorscheme
11. Refactor `MenuScreen` to use colorscheme
12. Refactor `SimpleScale` to use colorscheme
13. Refactor `ShotProfile` to use colorscheme
14. Test: Run app, verify everything works with Dark colorscheme

### Phase 3: Colorscheme Picker
15. Implement `ColorschemePickerScreen`
    - Layout with list and preview graph
    - UP/DOWN navigation
    - Live colorscheme updates
    - Save on exit (LEFT)
16. Test: Can run picker standalone, can change colorschemes

### Phase 4: Settings Menu Integration
17. Add Settings menu factory to `ScreenManager`
18. Add "Settings" option to main menu
19. Test: Can navigate Main → Settings → Colourscheme Picker → back

### Phase 5: Polish & Testing
20. Test all colorschemes across all screens
21. Test edge cases (missing files, invalid JSON, etc.)
22. Verify settings persistence across app restarts
23. Clean up any remaining hardcoded colors

## Edge Cases & Error Handling

**Missing files:**
- `config/default_settings.json` missing: Create with defaults
- `config/settings.json` missing: Create empty {} (use all defaults)
- `config/colorschemes.json` missing: Create with builtin colorschemes

**Invalid JSON:**
- Catch JSON parse errors, log warning, use defaults
- If user settings.json is corrupted, rename to settings.json.backup and create fresh

**Invalid colorscheme name:**
- If settings.json references non-existent colorscheme, fall back to default (Dark)

**Missing color slots:**
- If a colorscheme is missing a required color, use a fallback (e.g., magenta to make it obvious)

## Testing Strategy

**Manual testing checklist:**
- [ ] App starts with Dark colorscheme
- [ ] Can navigate to Settings → Colourscheme
- [ ] Can see all colorschemes in picker
- [ ] Colorscheme preview updates as I navigate UP/DOWN
- [ ] Pressing LEFT saves and returns to Settings menu
- [ ] Settings menu shows in new colorscheme
- [ ] Pressing LEFT returns to Main menu
- [ ] Main menu shows in new colorscheme
- [ ] Can enter Simple Scale, shows in new colorscheme
- [ ] Can enter Shot Profile, shows in new colorscheme
- [ ] Can change colorscheme again
- [ ] Settings persist after app restart
- [ ] All 5+ colorschemes look visually appealing

**Edge case testing:**
- [ ] Delete settings.json, restart app → creates new file with defaults
- [ ] Corrupt settings.json, restart app → handles gracefully
- [ ] Reference invalid colorscheme in settings.json → falls back to default

## File Locations Summary

```
SmartScaleIntegration/
├── config/                                    # Settings directory
│   ├── colorschemes.json                      # Colorscheme definitions
│   ├── default_settings.json                  # Default settings (tracked)
│   └── settings.json                          # User settings (can be gitignored)
├── src/
│   ├── settings/                              # Settings module (new)
│   │   ├── __init__.py                        # Exports SettingsManager, ColorScheme
│   │   ├── settings_manager.py                # SettingsManager class
│   │   └── colorscheme.py                     # ColorScheme class
│   ├── drivers/
│   │   └── ...
│   └── firmware/
│       ├── screens/
│       │   ├── base_screen.py                 # Add colorscheme property
│       │   ├── colorscheme_picker.py          # ColorschemePickerScreen (new)
│       │   ├── screen_manager.py              # Add Settings menu
│       │   └── ...
│       └── main.py
└── ...
```

## Color Slot Usage Reference

Quick reference for which colors to use where:

- **background**: Main screen background
- **foreground**: Primary text, borders, axes
- **primary_accent**: Menu highlights, primary interactive elements
- **secondary_accent**: First graph line, secondary interactive elements
- **tertiary_accent**: Second graph line, tertiary interactive elements
- **success**: Success messages ("Connected!")
- **error**: Error messages ("Connection Failed", no reading)
- **info**: Info messages ("Connecting...")

## Colorscheme Definitions

### Dark Theme
Inspired by VS Code Dark+
- background: #1e1e1e (dark gray)
- foreground: #d4d4d4 (light gray)
- primary_accent: #0e639c (blue - less bright than #007acc)
- secondary_accent: #4ec9b0 (teal)
- tertiary_accent: #ce9178 (salmon/orange)
- success: #4ec9b0 (teal)
- error: #f48771 (coral red)
- info: #569cd6 (light blue)

### Light Theme
Clean, high contrast
- background: #ffffff (white)
- foreground: #000000 (black)
- primary_accent: #0066cc (blue)
- secondary_accent: #0099cc (cyan)
- tertiary_accent: #cc6600 (orange)
- success: #00aa00 (green)
- error: #cc0000 (red)
- info: #0066cc (blue)

### Espresso Theme
Warm coffee/brown tones
- background: #2b1d16 (dark brown)
- foreground: #e8d5b7 (cream)
- primary_accent: #8b6f47 (mocha)
- secondary_accent: #c97a3a (caramel)
- tertiary_accent: #6b4423 (coffee)
- success: #8b6f47 (mocha)
- error: #b33c20 (rust)
- info: #c97a3a (caramel)

### Ocean Theme
Cool blues and teals
- background: #0a1929 (deep blue)
- foreground: #b3e5fc (light cyan)
- primary_accent: #00acc1 (cyan)
- secondary_accent: #29b6f6 (light blue)
- tertiary_accent: #26c6da (teal)
- success: #26a69a (sea green)
- error: #ef5350 (coral)
- info: #42a5f5 (blue)

### Sunset Theme
Warm oranges and purples
- background: #1a0a1f (deep purple)
- foreground: #ffe0b2 (light peach)
- primary_accent: #ff6f00 (orange)
- secondary_accent: #ff9800 (amber)
- tertiary_accent: #ab47bc (purple)
- success: #ffb74d (gold)
- error: #e53935 (red)
- info: #ff9800 (amber)

### Forest Theme
Natural greens and earth tones
- background: #1b2a1f (dark green)
- foreground: #e8f5e9 (light green)
- primary_accent: #558b2f (green)
- secondary_accent: #7cb342 (lime)
- tertiary_accent: #8d6e63 (brown)
- success: #66bb6a (bright green)
- error: #d84315 (rust)
- info: #7cb342 (lime)

## Potential Issues & Solutions

**Issue 1: Gray text in SimpleScale**
Current: gray hint text
Solution: Use foreground color (will be readable in all themes)
Alternative: Add `muted` color to colorscheme (foreground at 70% opacity)
Decision: Use foreground for now, can add muted later

**Issue 2: Menu highlight inversion**
Current: Highlighted item has black background, white text
Solution: primary_accent for background, background for text (inverted)
This should work well across all themes

**Issue 3: Axes and borders in graphs**
Current: Black
Solution: Use foreground
Should provide good contrast in all themes

**Issue 4: Font color with varied backgrounds**
Some backgrounds are very dark, some very light
Solution: Ensure all colorschemes have sufficient contrast between background and foreground
Test with actual display rendering

**Issue 5: Nested menu navigation confusion**
Three levels of menus might be confusing
Solution: Clear titles ("MAIN MENU", "SETTINGS", "CHOOSE COLOURSCHEME")
Consistent navigation (LEFT always goes back)

## Success Criteria

This implementation is successful if:
1. ✅ User can access Settings from main menu
2. ✅ User can change colorscheme via Colourscheme picker
3. ✅ All screens render correctly in all colorschemes
4. ✅ Colorscheme changes persist across app restarts
5. ✅ No hardcoded colors remain in any screen code
6. ✅ Settings system is extensible for future settings
7. ✅ Code is clean, well-documented, and follows existing patterns
8. ✅ All colorschemes are visually appealing and readable

## Next Steps After This Implementation

Future enhancements (not in scope now):
- Add more settings (display brightness, timer beep, etc.)
- Add colorscheme editor
- Import/export colorschemes
- Preview colorscheme on other screens (not just picker)
- Animation/transitions when changing colorschemes

---

## Ready to Implement

This plan is comprehensive and well-reasoned. I'm confident in the approach and ready to execute systematically through the 5 phases.
