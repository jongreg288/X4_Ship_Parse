#!/usr/bin/env python3
"""
Build script for X4 ShipMatrix executable
Creates a standalone .exe file using PyInstaller
"""

import subprocess
import sys
from pathlib import Path
import shutil

def main():
    """Build the X4 ShipMatrix executable."""
    print("🔨 Building X4 ShipMatrix executable...")
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    
    # Check if PyInstaller is installed
    try:
        subprocess.run([sys.executable, "-c", "import PyInstaller"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller installed successfully!")
    
    # Clean previous build
    build_dir = project_root / "build"
    
    if build_dir.exists():
        print("🧹 Cleaning previous build directory...")
        shutil.rmtree(build_dir)
    
    # Build the executable
    spec_file = project_root / "X4_ShipMatrix.spec"
    
    if not spec_file.exists():
        print("❌ X4_ShipMatrix.spec not found!")
        return False
    
    # Build directly to build_scripts folder
    
    print("🏗️ Building executable...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--distpath", str(project_root),
            str(spec_file)
        ], check=True, cwd=project_root)
        
        exe_path = project_root / "X4 ShipMatrix.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✅ Build successful!")
            print(f"📦 Executable created: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            print(f"🚀 You can now distribute 'X4 ShipMatrix.exe' as a standalone application!")
            return True
        else:
            print("❌ Build completed but executable not found!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)