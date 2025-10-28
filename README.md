# X4 Ship Parse

A Python application for parsing and analyzing X4: Foundations ship data from game XML files.

## Features

- Parse ship and engine data from X4 XML files
- Calculate realistic travel speeds using physics formulas
- GUI interface for comparing ships and engines
- Support for multiple engine configurations
- Extract mass, drag, and engine connection data

## For End Users (Standalone Version)

If you downloaded the standalone executable:

1. **Download** the X4ShipParse.exe file
2. **Run** X4ShipParse.exe
3. **Follow the setup wizard** - it will automatically:
   - Detect your X4: Foundations installation
   - Extract the required XML data files
   - Set up the application for use

**Requirements:**
- Windows 10/11
- X4: Foundations installed (Steam, Epic Games, or GOG)

## For Developers (Source Code)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Game Data Setup

This application requires X4: Foundations game data files. The app can automatically extract these, or you can set them up manually:

**Required Directory Structure:**
```
data/
├── assets/
│   ├── props/
│   │   └── Engines/
│   │       └── macros/
│   │           └── *.xml (engine definition files)
│   └── units/
│       ├── size_l/
│       │   ├── *.xml (large ship component files)
│       │   └── macros/
│       │       └── *.xml (large ship macro files)
│       ├── size_m/
│       │   ├── *.xml (medium ship component files)
│       │   └── macros/
│       │       └── *.xml (medium ship macro files)
│       └── size_s/
│           ├── *.xml (small ship component files)
│           └── macros/
│               └── *.xml (small ship macro files)
```

**Where to find X4 data files:**
- Steam: `Steam\steamapps\common\X4 Foundations\`
- Extract from game archives or use modding tools
- Files are typically in compressed/packed format and need extraction

### 3. Run the Application

```bash
python main.py
```

## Usage

1. **Launch the GUI**: Run `python main.py`
2. **Select Ship**: Choose a ship from the dropdown (or "None")
3. **Select Engine**: Choose an engine from the dropdown (or "None")
4. **View Stats**: See calculated travel speed and ship specifications

## Travel Speed Formula

The application calculates travel speed using:

```
travel_speed = (forward_thrust × travel_thrust × engine_connections) / drag_forward
```

Where:
- `forward_thrust`: Engine's forward thrust value
- `travel_thrust`: Engine's travel drive thrust
- `engine_connections`: Number of engine mount points on the ship
- `drag_forward`: Ship's forward drag coefficient

## Files

- `main.py`: Application entry point
- `app/data_parser.py`: XML parsing logic for ships and engines
- `app/logic.py`: Travel speed calculation formulas
- `app/gui.py`: PyQt6 GUI interface
- `requirements.txt`: Python dependencies

## Building Standalone Executable

To create a distributable .exe file:

```bash
python build_exe.py
```

This will:
1. Install PyInstaller if needed
2. Clean previous builds
3. Build X4_Ship_Parser.exe in the `dist` folder (~62 MB)
4. Create a standalone executable that includes all dependencies

**The executable includes:**
- Complete PyQt6 GUI with 4-tab interface
- X4 text localization system (71,096+ mappings)  
- Advanced ship name resolution
- All Python dependencies bundled
- No installation required - just run X4_Ship_Parser.exe

**Requirements for end users:**
- Windows 10/11 64-bit
- X4: Foundations game files (for data extraction)

## Development

To add debug output or modify parsing:

1. Edit `debug_parser.py` for testing without GUI
2. Modify formulas in `app/logic.py`
3. Update parsing logic in `app/data_parser.py`
4. Use `launcher.py` for testing the full user experience

## License

This project is for educational/modding purposes. X4: Foundations and its data files are property of Egosoft.