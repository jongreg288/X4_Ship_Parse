"""
Build script for X4 ShipMatrix with separate updater
Creates both the main application and optional updater executable
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command with error handling."""
    print(f"🔨 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Error: {e.stderr}")
        return False

def clean_build_directories():
    """Clean previous build directories."""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"🧹 Cleaning {dir_name} directory...")
            shutil.rmtree(dir_path)

def install_pyinstaller():
    """Install PyInstaller if not available."""
    try:
        import PyInstaller
        print("✅ PyInstaller already installed")
        return True
    except ImportError:
        print("📦 PyInstaller not found, installing...")
        return run_command([sys.executable, "-m", "pip", "install", "PyInstaller"], 
                          "Installing PyInstaller")

def build_main_executable():
    """Build the main X4 ShipMatrix executable."""
    return run_command([sys.executable, "-m", "PyInstaller", "X4_ShipMatrix.spec"], 
                      "Building main X4 ShipMatrix.exe")

def build_updater_executable():
    """Build the optional updater executable."""
    return run_command([sys.executable, "-m", "PyInstaller", "X4_Updater.spec"], 
                      "Building X4_Updater.exe")

def get_file_sizes():
    """Get and display file sizes."""
    dist_dir = Path("dist")
    
    main_exe = dist_dir / "X4 ShipMatrix.exe"
    updater_exe = dist_dir / "X4_Updater.exe"
    
    sizes = {}
    if main_exe.exists():
        size_mb = main_exe.stat().st_size / (1024 * 1024)
        sizes["X4 ShipMatrix.exe"] = f"{size_mb:.1f} MB"
    
    if updater_exe.exists():
        size_mb = updater_exe.stat().st_size / (1024 * 1024)
        sizes["X4_Updater.exe"] = f"{size_mb:.1f} MB"
    
    return sizes

def main():
    """Main build process."""
    print("🔨 Building X4 ShipMatrix with Optional Updater")
    print("=" * 50)
    
    # Change to build_scripts directory
    script_dir = Path(__file__).parent
    original_dir = os.getcwd()
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    try:
        # Check prerequisites
        if not install_pyinstaller():
            print("❌ Build failed: Could not install PyInstaller")
            return 1
        
        # Clean previous builds
        clean_build_directories()
        
        # Build main executable
        if not build_main_executable():
            print("❌ Build failed: Main executable build failed")
            return 1
        
        # Build updater executable (continue even if this fails)
        print("\n📡 Building optional updater executable...")
        updater_success = build_updater_executable()
        if not updater_success:
            print("⚠️ Updater build failed - continuing without updater")
        
        # Show results
        sizes = get_file_sizes()
        print("\n🎉 Build Results:")
        print("-" * 30)
        for filename, size in sizes.items():
            print(f"📦 {filename}: {size}")
        
        print(f"\n✅ Build completed!")
        print(f"📁 Files available in: {Path('dist').absolute()}")
        
        if "X4_Updater.exe" in sizes:
            print("\n💡 Update Options:")
            print("   • Distribute both executables for automatic update checking")
            print("   • Distribute only 'X4 ShipMatrix.exe' for manual updates")
            print("   • Users can check updates via Help → Check for Updates")
        else:
            print("\n💡 Update Method:")
            print("   • Manual updates only (Help → Check for Updates opens GitHub)")
            print("   • Users download new versions from GitHub releases")
        
        return 0
    
    finally:
        # Restore original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    sys.exit(main())