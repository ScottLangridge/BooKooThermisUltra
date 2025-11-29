# Navigation Fix - Settings Menu Issue

## Problem
When navigating Main Menu → Settings → Colourscheme, the app would jump back to Main Menu instead of showing the Colourscheme Picker.

## Root Cause
The Settings menu was using the same `selected_screen` mechanism as the Main Menu. When an option was selected in Settings, it would:
1. Set `selected_screen` to the picker
2. Stop the Settings menu
3. Return control to the main loop
4. Main loop would go back to `show_menu()` (Main Menu) instead of running the picker

## Solution
Created a dedicated `SettingsScreen` class that manages its own internal navigation loop.

### New File
`src/firmware/screens/settings_screen.py`
- Extends `BaseScreen`
- Contains its own navigation loop
- When Colourscheme is selected, runs the picker directly
- When picker returns (LEFT pressed), shows Settings menu again
- When LEFT is pressed in Settings menu, returns to Main Menu

### Changes to ScreenManager
Simplified `select_settings()` callback to use `SettingsScreen` class instead of factory function.

## Navigation Flow (Fixed)
```
Main Menu
  │
  ├─ (RIGHT/CENTER on "Settings")
  │
  ↓
Settings Menu
  │
  ├─ (RIGHT/CENTER on "Colourscheme")
  │
  ↓
Colourscheme Picker
  │
  ├─ (LEFT to go back)
  │
  ↓
Settings Menu  ← Returns here correctly!
  │
  ├─ (LEFT to go back)
  │
  ↓
Main Menu  ← Returns here correctly!
```

## Files Modified
1. **New**: `src/firmware/screens/settings_screen.py`
2. **Modified**: `src/firmware/screens/screen_manager.py` (simplified settings callback)

## Testing
Verified that:
- ✅ All imports work
- ✅ Navigation flow is correct
- ✅ LEFT button works in both Settings menu and Picker
- ✅ No infinite loops or stuck states

## Status
**FIXED** - Ready to test!
