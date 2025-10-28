"""
Build script for X4 Ship Parser with separate updater
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
    """Build the main X4 Ship Parser executable."""
    return run_command([sys.executable, "-m", "PyInstaller", "X4_Ship_Parser.spec"], 
                      "Building main X4_Ship_Parser.exe")

def build_updater_executable():
    """Build the optional updater executable."""
    return run_command([sys.executable, "-m", "PyInstaller", "X4_Updater.spec"], 
                      "Building X4_Updater.exe")

def copy_to_distro():
    """Copy executables to distro directory."""
    distro_dir = Path("../distro")
    distro_dir.mkdir(exist_ok=True)
    
    # Copy main executable
    main_exe = Path("dist/X4_Ship_Parser.exe")
    if main_exe.exists():
        shutil.copy2(main_exe, distro_dir / "X4_Ship_Parser.exe")
        print("✅ Copied X4_Ship_Parser.exe to distro directory")
    
    # Copy updater executable (optional)
    updater_exe = Path("dist/X4_Updater.exe")
    if updater_exe.exists():
        shutil.copy2(updater_exe, distro_dir / "X4_Updater.exe")
        print("✅ Copied X4_Updater.exe to distro directory")

def get_file_sizes():
    """Get and display file sizes."""
    distro_dir = Path("../distro")
    
    main_exe = distro_dir / "X4_Ship_Parser.exe"
    updater_exe = distro_dir / "X4_Updater.exe"
    
    sizes = {}
    if main_exe.exists():
        size_mb = main_exe.stat().st_size / (1024 * 1024)
        sizes["X4_Ship_Parser.exe"] = f"{size_mb:.1f} MB"
    
    if updater_exe.exists():
        size_mb = updater_exe.stat().st_size / (1024 * 1024)
        sizes["X4_Updater.exe"] = f"{size_mb:.1f} MB"
    
    return sizes

def main():
    """Main build process."""
    print("🔨 Building X4 Ship Parser with Optional Updater")
    print("=" * 50)
    
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
    
    # Copy to distro
    copy_to_distro()
    
    # Show results
    sizes = get_file_sizes()
    print("\n🎉 Build Results:")
    print("-" * 30)
    for filename, size in sizes.items():
        print(f"📦 {filename}: {size}")
    
    print(f"\n✅ Build completed!")
    print(f"📁 Files available in: {Path('../distro').absolute()}")
    
    if "X4_Updater.exe" in sizes:
        print("\n💡 Update Options:")
        print("   • Distribute both executables for automatic update checking")
        print("   • Distribute only X4_Ship_Parser.exe for manual updates")
        print("   • Users can check updates via Help → Check for Updates")
    else:
        print("\n💡 Update Method:")
        print("   • Manual updates only (Help → Check for Updates opens GitHub)")
        print("   • Users download new versions from GitHub releases")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())