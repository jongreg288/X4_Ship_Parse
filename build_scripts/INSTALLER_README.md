# Building the X4 ShipMatrix Installer

This directory contains the Inno Setup script for creating a professional Windows installer.

## Prerequisites

1. **Download and Install Inno Setup**:
   - Visit: https://jrsoftware.org/isdl.php
   - Download: Inno Setup 6.x (Latest version)
   - Install with default options

## Building the Installer

### Method 1: Using Inno Setup GUI (Easiest)

1. Open Inno Setup Compiler
2. File → Open → Select `X4_ShipMatrix_Setup.iss`
3. Build → Compile (or press F9)
4. The installer will be created in: `releases/latest/X4_ShipMatrix_v0.1.3_Setup.exe`

### Method 2: Using Command Line

```powershell
# Run from the build_scripts directory
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" X4_ShipMatrix_Setup.iss
```

### Method 3: Using Python Build Script (Automated)

```powershell
# From project root
python build_scripts\build_installer.py
```

## What Gets Included

The installer packages:
- ✅ X4 ShipMatrix.exe (78.4 MB)
- ✅ X4_Updater.exe (14.4 MB)
- ✅ XRCatTool.exe and XRCatToolGUI.exe
- ✅ README files and documentation
- ✅ data/ directory (if present)

## Installer Features

- 📦 Single-file installer (~93 MB compressed)
- 🎯 Professional Windows installer experience
- 🖥️ Creates Start Menu shortcuts
- 💻 Optional Desktop shortcut
- 🗑️ Built-in uninstaller
- 📝 License agreement display
- ℹ️ Welcome screen with app info
- 🔧 Custom installation directory option

## Output

After compilation, you'll get:
- **File**: `releases/latest/X4_ShipMatrix_v0.1.3_Setup.exe`
- **Size**: ~93 MB (compressed from 93 MB total)
- **Compatibility**: Windows 10/11 (64-bit)

## Distribution

Distribute the single Setup.exe file to users. They simply:
1. Download `X4_ShipMatrix_v0.1.3_Setup.exe`
2. Run the installer
3. Follow the wizard
4. Launch from Start Menu or Desktop

## Notes

- The installer uses LZMA2 ultra compression for smallest file size
- Requires 64-bit Windows (x64 architecture)
- Can install for all users (requires admin) or current user only
- Automatically creates uninstaller entry in Windows Settings
