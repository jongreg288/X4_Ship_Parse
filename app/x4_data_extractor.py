"""
X4 Game Data Detection and Extraction Module

This module handles:
1. Finding X4 installation directories
2. Extracting XML files from game archives
3. Setting up the data directory structure
"""

import os
import sys
import winreg
from pathlib import Path
from typing import List, Optional
import zipfile
import subprocess
import json


class X4DataExtractor:
    """Handles detection and extraction of X4 game data files."""
    
    def __init__(self):
        self.x4_install_path: Optional[Path] = None
        self.data_dir = Path("data")
        
    def find_x4_installation(self) -> Optional[Path]:
        """
        Find X4: Foundations installation directory by checking:
        1. Steam registry keys
        2. Common Steam library locations
        3. Epic Games Store locations
        4. GOG locations
        """
        possible_paths = []
        
        # Check Steam registry
        steam_paths = self._get_steam_paths()
        possible_paths.extend(steam_paths)
        
        # Check common installation directories
        common_paths = [
            Path("C:/Program Files (x86)/Steam/steamapps/common/X4 Foundations"),
            Path("C:/Program Files/Steam/steamapps/common/X4 Foundations"),
            Path("C:/Steam/steamapps/common/X4 Foundations"),
            Path("D:/Steam/steamapps/common/X4 Foundations"),
            Path("E:/Steam/steamapps/common/X4 Foundations"),
            # Epic Games Store
            Path("C:/Program Files/Epic Games/X4 Foundations"),
            # GOG
            Path("C:/Program Files (x86)/GOG Galaxy/Games/X4 Foundations"),
            Path("C:/GOG Games/X4 Foundations"),
        ]
        possible_paths.extend(common_paths)
        
        # Check each path for X4.exe
        for path in possible_paths:
            if path.exists() and (path / "X4.exe").exists():
                print(f"✅ Found X4 installation at: {path}")
                self.x4_install_path = path
                return path
                
        return None
    
    def _get_steam_paths(self) -> List[Path]:
        """Get Steam library paths from registry and config files."""
        steam_paths = []
        
        try:
            # Try to get Steam install path from registry
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                steam_root = Path(steam_path)
                
                # Check main Steam library
                x4_path = steam_root / "steamapps/common/X4 Foundations"
                steam_paths.append(x4_path)
                
                # Check additional Steam library folders
                library_folders_file = steam_root / "steamapps/libraryfolders.vdf"
                if library_folders_file.exists():
                    additional_paths = self._parse_steam_library_folders(library_folders_file)
                    steam_paths.extend(additional_paths)
                    
        except (OSError, FileNotFoundError):
            pass  # Registry key not found or Steam not installed
            
        return steam_paths
    
    def _parse_steam_library_folders(self, vdf_file: Path) -> List[Path]:
        """Parse Steam's libraryfolders.vdf to find additional Steam libraries."""
        paths = []
        
        try:
            with open(vdf_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple VDF parsing for library paths
            lines = content.split('\n')
            for line in lines:
                if '"path"' in line:
                    # Extract path from "path"		"C:\\Steam"
                    parts = line.split('"')
                    if len(parts) >= 4:
                        library_path = Path(parts[3].replace('\\\\', '\\'))
                        x4_path = library_path / "steamapps/common/X4 Foundations"
                        paths.append(x4_path)
                        
        except Exception as e:
            print(f"Warning: Could not parse Steam library folders: {e}")
            
        return paths
    
    def extract_xml_files(self) -> bool:
        """
        Extract XML files from X4 game archives.
        X4 stores data in .cat/.dat file pairs that need special extraction.
        """
        if not self.x4_install_path:
            print("❌ X4 installation path not found")
            return False
            
        print("🔄 Extracting XML files from X4 game data...")
        
        # Look for .cat/.dat files in the game directory
        cat_files = list(self.x4_install_path.glob("*.cat"))
        
        if not cat_files:
            print("❌ No .cat files found in X4 installation")
            return False
            
        # Try to use XStudio or other X4 modding tools if available
        success = self._extract_with_external_tools(cat_files)
        
        if not success:
            # Fallback: look for unpacked files or provide instructions
            success = self._check_for_unpacked_files()
            
        return success
    
    def _extract_with_external_tools(self, cat_files: List[Path]) -> bool:
        """Try to extract using external X4 modding tools."""
        
        if not self.x4_install_path:
            return False
            
        # Check for XR Catalog Tool (common X4 modding tool)
        possible_extractors = [
            "XRCatalogTool.exe",
            "X4_DataExtractionTool.exe",
            "x4_extractor.exe"
        ]
        
        extractor_path = None
        for tool in possible_extractors:
            # Check in X4 directory
            tool_path = self.x4_install_path / tool
            if tool_path.exists():
                extractor_path = tool_path
                break
                
            # Check in common tools directories
            for tools_dir in ["tools", "modding", "utils"]:
                tool_path = self.x4_install_path / tools_dir / tool
                if tool_path.exists():
                    extractor_path = tool_path
                    break
                    
        if extractor_path:
            try:
                # Run the extraction tool
                subprocess.run([
                    str(extractor_path),
                    "--extract-xml",
                    "--output", str(self.data_dir.absolute())
                ], check=True)
                print("✅ Successfully extracted XML files using external tool")
                return True
            except subprocess.CalledProcessError:
                print("⚠️ External extraction tool failed")
                
        return False
    
    def _check_for_unpacked_files(self) -> bool:
        """Check if XML files are already unpacked in the game directory."""
        
        if not self.x4_install_path:
            return False
            
        # Some X4 installations have unpacked files
        possible_data_dirs = [
            self.x4_install_path / "assets",
            self.x4_install_path / "data",
            self.x4_install_path / "unpacked",
            self.x4_install_path / "extracted"
        ]
        
        for data_dir in possible_data_dirs:
            if data_dir.exists():
                # Look for the XML structure we need
                engines_dir = data_dir / "assets/props/Engines/macros"
                ships_dir = data_dir / "assets/units"
                
                if engines_dir.exists() and ships_dir.exists():
                    print(f"✅ Found unpacked XML files at: {data_dir}")
                    # Copy files to our data directory
                    return self._copy_xml_files(data_dir)
                    
        return False
    
    def _copy_xml_files(self, source_dir: Path) -> bool:
        """Copy XML files from source to our data directory."""
        import shutil
        
        try:
            # Create our data directory structure
            self.data_dir.mkdir(exist_ok=True)
            target_assets = self.data_dir / "assets"
            target_assets.mkdir(exist_ok=True)
            
            # Copy engines
            source_engines = source_dir / "assets/props/Engines"
            target_engines = target_assets / "props/Engines"
            if source_engines.exists():
                shutil.copytree(source_engines, target_engines, dirs_exist_ok=True)
                print("✅ Copied engine XML files")
                
            # Copy ships
            source_units = source_dir / "assets/units"
            target_units = target_assets / "units"
            if source_units.exists():
                shutil.copytree(source_units, target_units, dirs_exist_ok=True)
                print("✅ Copied ship XML files")
                
            return True
            
        except Exception as e:
            print(f"❌ Error copying XML files: {e}")
            return False
    
    def setup_data_directory(self) -> bool:
        """Set up the data directory with X4 files."""
        
        # First, try to find X4 installation
        x4_path = self.find_x4_installation()
        
        if not x4_path:
            print("❌ Could not find X4: Foundations installation")
            print("Please install X4: Foundations or specify the installation path manually")
            return False
            
        # Try to extract XML files
        success = self.extract_xml_files()
        
        if not success:
            print("\n📋 Manual Setup Instructions:")
            print("─" * 50)
            print(f"X4 Installation found at: {x4_path}")
            print("\nTo manually extract XML files:")
            print("1. Use X4 modding tools like XR Catalog Tool")
            print("2. Extract .cat files to get XML data")
            print("3. Copy extracted files to the 'data' folder")
            print("4. Ensure this structure:")
            print("   data/assets/props/Engines/macros/*.xml")
            print("   data/assets/units/size_*/macros/*.xml")
            
        return success
    
    def validate_data_directory(self) -> bool:
        """Check if the data directory has the required XML files."""
        
        required_paths = [
            self.data_dir / "assets/props/Engines/macros",
            self.data_dir / "assets/units/size_l/macros",
            self.data_dir / "assets/units/size_m/macros",
            self.data_dir / "assets/units/size_s/macros"
        ]
        
        for path in required_paths:
            if not path.exists():
                print(f"❌ Missing required directory: {path}")
                return False
                
            # Check for XML files
            xml_files = list(path.glob("*.xml"))
            if not xml_files:
                print(f"❌ No XML files found in: {path}")
                return False
                
        print("✅ Data directory validation passed")
        return True


def setup_x4_data() -> bool:
    """Main function to set up X4 data for the application."""
    
    print("🚀 X4 Ship Parse - Data Setup")
    print("=" * 40)
    
    extractor = X4DataExtractor()
    
    # Check if data directory already exists and is valid
    if extractor.validate_data_directory():
        print("✅ X4 data already set up and valid")
        return True
        
    print("🔍 Setting up X4 game data...")
    success = extractor.setup_data_directory()
    
    if success:
        print("✅ X4 data setup completed successfully!")
    else:
        print("❌ X4 data setup failed. Manual setup may be required.")
        
    return success


if __name__ == "__main__":
    setup_x4_data()