#!/usr/bin/env python3
"""
Prepare all files needed for the X4 ShipMatrix installer
This script copies all required files to the dist folder for packaging
"""

import shutil
import sys
from pathlib import Path

def main():
    """Prepare files for installer."""
    print("📋 Preparing X4 ShipMatrix Installer Files...")
    print("=" * 50)
    
    # Set up paths
    build_scripts_dir = Path(__file__).parent
    project_root = build_scripts_dir.parent
    dist_dir = build_scripts_dir / "dist"
    
    # Create dist directory
    if dist_dir.exists():
        print("🧹 Cleaning previous dist directory...")
        shutil.rmtree(dist_dir)
    
    dist_dir.mkdir(exist_ok=True)
    print(f"✅ Created dist directory: {dist_dir}")
    
    files_copied = []
    
    # Copy main executable
    main_exe_source = build_scripts_dir / "X4 ShipMatrix.exe"
    if main_exe_source.exists():
        main_exe_dest = dist_dir / "X4 ShipMatrix.exe"
        shutil.copy2(main_exe_source, main_exe_dest)
        size_mb = main_exe_dest.stat().st_size / (1024 * 1024)
        files_copied.append(f"X4 ShipMatrix.exe ({size_mb:.1f} MB)")
        print(f"✅ Copied main executable: X4 ShipMatrix.exe ({size_mb:.1f} MB)")
    else:
        print(f"❌ Main executable not found: {main_exe_source}")
        print("   Please build the main executable first using build_exe.py")
        return 1
    
    # Copy updater executable (optional)
    updater_source_paths = [
        build_scripts_dir / "X4_Updater.exe",
        project_root / "X4_Updater.exe"
    ]
    
    updater_copied = False
    for updater_source in updater_source_paths:
        if updater_source.exists():
            updater_dest = dist_dir / "X4_Updater.exe"
            shutil.copy2(updater_source, updater_dest)
            size_mb = updater_dest.stat().st_size / (1024 * 1024)
            files_copied.append(f"X4_Updater.exe ({size_mb:.1f} MB)")
            print(f"✅ Copied updater executable: X4_Updater.exe ({size_mb:.1f} MB)")
            updater_copied = True
            break
    
    if not updater_copied:
        print("⚠️ Updater executable not found - installer will be main app only")
        print("   Build updater with: python build_both.py")
    
    # Copy README for users
    readme_source = build_scripts_dir / "README_USERS.txt"
    if readme_source.exists():
        readme_dest = dist_dir / "README_USERS.txt"
        shutil.copy2(readme_source, readme_dest)
        size_kb = readme_dest.stat().st_size / 1024
        files_copied.append(f"README_USERS.txt ({size_kb:.1f} KB)")
        print(f"✅ Copied user documentation: README_USERS.txt ({size_kb:.1f} KB)")
    else:
        print(f"❌ README_USERS.txt not found: {readme_source}")
        return 1
    
    # Show summary
    print("\n🎉 Files prepared for installer:")
    print("-" * 40)
    for file_info in files_copied:
        print(f"📦 {file_info}")
    
    # Calculate total size
    total_size_mb = 0
    for file_info in files_copied:
        filename = file_info.split()[0]
        file_path = dist_dir / filename
        if file_path.exists():
            total_size_mb += file_path.stat().st_size / (1024 * 1024)
    
    print(f"\n📏 Total package size: {total_size_mb:.1f} MB")
    print(f"📁 Files ready in: {dist_dir}")
    print(f"\n✅ Ready to build installer with build_installer.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())