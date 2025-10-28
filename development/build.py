"""
Build script for creating a standalone X4 Ship Parse executable.
Uses PyInstaller to create a distributable .exe file.
"""

import subprocess
import sys
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_executable():
    """Build the standalone executable."""
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--windowed",                   # No console window (for GUI app)
        "--name", "X4ShipParse",       # Executable name
        "--icon", "icon.ico",          # Icon file (if exists)
        "--add-data", "README.md;.",   # Include README
        "--add-data", "requirements.txt;.",  # Include requirements
        "--hidden-import", "pandas",   # Ensure pandas is included
        "--hidden-import", "PyQt6",    # Ensure PyQt6 is included
        "--collect-all", "PyQt6",      # Include all PyQt6 components
        "launcher.py"                  # Main script
    ]
    
    # Remove icon parameter if icon file doesn't exist
    if not Path("icon.ico").exists():
        cmd.remove("--icon")
        cmd.remove("icon.ico")
    
    print("🔨 Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("✅ Build completed successfully!")
        print("📁 Executable created: dist/X4ShipParse.exe")
        
        # Instructions for distribution
        print("\n📋 Distribution Instructions:")
        print("─" * 40)
        print("1. The executable is in the 'dist' folder")
        print("2. Users will need to:")
        print("   - Have X4: Foundations installed")
        print("   - Run X4ShipParse.exe")
        print("   - Follow the setup wizard to extract game data")
        print("3. The app will auto-detect X4 and extract XML files")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
        
    return True


def create_installer_script():
    """Create a simple installer script."""
    
    installer_content = '''
@echo off
echo X4 Ship Parse - Installation
echo ============================

echo.
echo This will install X4 Ship Parse on your system.
echo.

REM Create installation directory
set INSTALL_DIR=%LOCALAPPDATA%\\X4ShipParse
echo Creating installation directory: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

REM Copy executable
echo Copying files...
copy "X4ShipParse.exe" "%INSTALL_DIR%\\" >nul
copy "README.md" "%INSTALL_DIR%\\" >nul

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\X4 Ship Parse.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\X4ShipParse.exe'; $Shortcut.Save()"

REM Create start menu shortcut
echo Creating start menu shortcut...
mkdir "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\X4 Ship Parse" 2>nul
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\X4 Ship Parse\\X4 Ship Parse.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\X4ShipParse.exe'; $Shortcut.Save()"

echo.
echo ✅ Installation completed successfully!
echo.
echo You can now run X4 Ship Parse from:
echo - Desktop shortcut
echo - Start menu
echo - %INSTALL_DIR%\\X4ShipParse.exe
echo.
pause
'''
    
    with open("install.bat", "w") as f:
        f.write(installer_content)
        
    print("✅ Created install.bat")


def main():
    """Main build function."""
    print("🏗️ X4 Ship Parse - Build System")
    print("=" * 35)
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Build executable
    success = build_executable()
    
    if success:
        # Create installer script
        create_installer_script()
        
        print("\n🎉 Build process completed!")
        print("\nFiles created:")
        print("- dist/X4ShipParse.exe (main executable)")
        print("- install.bat (installer script)")
        
        print("\n📦 To distribute:")
        print("1. Zip the contents of the 'dist' folder")
        print("2. Include install.bat for easy installation")
        print("3. Users run install.bat to set up shortcuts")
        
    else:
        print("❌ Build failed. Check error messages above.")


if __name__ == "__main__":
    main()