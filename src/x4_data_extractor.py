"""
X4 Game Data Detection and Extraction Module

This module handles:
1. Finding X4 installation directories
2. Extracting XML files from game archives
3. Setting up the data directory structure
4. Language-aware extraction
"""

import os
import sys
import winreg
from pathlib import Path
from typing import List, Optional
import zipfile
import subprocess
import json
from .language_detector import language_detector

def safe_print(message):
    """Print that works in both console and executable mode."""
    try:
        if sys.stdout is not None:
            print(message)
    except (AttributeError, OSError):
        # If print fails, silently continue (executable mode)
        pass

# Import loading dialog functions (with fallback if not available)
try:
    from .loading_dialog import update_loading_status
except ImportError:
    def update_loading_status(message: str):
        pass  # Fallback for when loading_dialog is not available


class X4DataExtractor:
    """Handles detection and extraction of X4 game data files."""
    
    def __init__(self):
        self.x4_install_path: Optional[Path] = None
        self.data_dir = Path("data")
        
    def _find_development_data(self) -> Optional[Path]:
        """Find data directory from development folder when running as executable."""
        
        # Get the current executable/script directory
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller executable
            current_dir = Path(sys.executable).parent
        else:
            # Running as script
            current_dir = Path(__file__).parent.parent
        
        # Look for development folder with data
        possible_dev_paths = [
            current_dir.parent / "development" / "data",  # ../development/data from distro
            current_dir / "development" / "data",         # development/data from current
            current_dir / "data",                         # data in current directory
        ]
        
        for dev_data_path in possible_dev_paths:
            if dev_data_path.exists():
                engines_dir = dev_data_path / "assets/props/Engines/macros"
                ships_dir = dev_data_path / "assets/units"
                
                if engines_dir.exists() and ships_dir.exists():
                    safe_print(f"✅ Found development data at: {dev_data_path}")
                    update_loading_status("✅ Found existing X4 data files")
                    return dev_data_path
                    
        return None
        
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
                safe_print(f"✅ Found X4 installation at: {path}")
                update_loading_status(f"✅ Found X4 installation")
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
            safe_print(f"Warning: Could not parse Steam library folders: {e}")
            
        return paths
    
    def _find_bundled_xrcattool(self) -> Optional[Path]:
        """Find the bundled XRCatTool.exe that ships with our application."""
        
        # Get the current executable/script directory
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller executable - XRCatTool should be in same dir as exe
            app_dir = Path(sys.executable).parent
        else:
            # Running as script - look relative to this file
            app_dir = Path(__file__).parent.parent
        
        # Possible locations for XRCatTool.exe
        possible_paths = [
            app_dir / "XRCatTool.exe",                    # Same directory as exe
            app_dir / "tools" / "XRCatTool.exe",          # tools subdirectory
            app_dir.parent / "distro" / "XRCatTool.exe",  # ../distro/ (when running from development)
        ]
        
        for tool_path in possible_paths:
            if tool_path.exists():
                safe_print(f"✅ Found bundled XRCatTool at: {tool_path}")
                return tool_path
            
        safe_print("⚠️ Bundled XRCatTool.exe not found")
        return None
        
    def extract_xml_files(self) -> bool:
        """
        Extract XML files from X4 game archives.
        X4 stores data in .cat/.dat file pairs that need special extraction.
        """
        if not self.x4_install_path:
            safe_print("❌ X4 installation path not found")
            return False
            
        safe_print("🔄 Extracting XML files from X4 game data...")
        
        # Look for .cat/.dat files in the game directory
        cat_files = list(self.x4_install_path.glob("*.cat"))
        
        if not cat_files:
            safe_print("❌ No .cat files found in X4 installation")
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
            
        # First, check for bundled XRCatTool.exe (included with our application)
        extractor_path = self._find_bundled_xrcattool()
        
        if not extractor_path:
            # Fallback: Check for other X4 modding tools
            possible_extractors = [
                "XRCatalogTool.exe",
                "XRCatTool.exe", 
                "X4_DataExtractionTool.exe",
                "x4_extractor.exe"
            ]
            
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
            return self._extract_with_xrcattool(extractor_path, cat_files)
                
        return False
    
    def _extract_with_xrcattool(self, tool_path: Path, cat_files: List[Path]) -> bool:
        """Extract XML files using XRCatTool.exe."""
        
        try:
            # Create output directory
            self.data_dir.mkdir(exist_ok=True)
            
            safe_print(f"🔧 Using XRCatTool: {tool_path}")
            safe_print(f"📁 Extracting to: {self.data_dir.absolute()}")
            
            # XRCatTool command: XRCatTool -in <cat_files> -out <output_dir> -include <patterns>
            # Extract only the specific files needed for ship parsing
            cmd = [
                str(tool_path),
                "-in"
            ]
            
            # Add all cat files as input
            for cat_file in cat_files:
                cmd.append(str(cat_file))
                
            cmd.extend([
                "-out", str(self.data_dir.absolute()),
                # Extract all necessary files:
                # 1. All translation files in \data\t
                "-include", r"^t/.*$",
                # 2. Index files (components.xml, macros.xml)
                "-include", r"^index/.*\.xml$",
                # 3. All files in size_l, size_m, size_s, size_xl directories (excluding size_xs)
                "-include", r"^assets/units/size_l/.*$",
                "-include", r"^assets/units/size_m/.*$",
                "-include", r"^assets/units/size_s/.*$",
                "-include", r"^assets/units/size_xl/.*$",
                # 4. All engine files
                "-include", r"^assets/props/Engines/.*$",
                # 5. All storage module files
                "-include", r"^assets/props/StorageModules/.*$"
            ])
            
            # Detect language for logging purposes
            detected_lang_id = language_detector.get_language_id(Path(self.x4_install_path) if self.x4_install_path else None)
            lang_name = language_detector.get_language_name(detected_lang_id)
            
            safe_print(f"🌍 Detected language: {lang_name} (ID: {detected_lang_id})")
            safe_print(f"📝 Will extract all translation files from t/")
            
            safe_print("🚀 Starting extraction...")
            safe_print(f"Command: {' '.join(cmd)}")
            update_loading_status("🔄 Extracting ship and engine data from X4 archives...")
            
            # Run XRCatTool
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  check=True,
                                  cwd=str(tool_path.parent))
            
            safe_print("✅ XRCatTool extraction completed successfully")
            
            # Verify that we got the files we need
            engines_dir = self.data_dir / "assets/props/Engines"
            storage_dir = self.data_dir / "assets/props/StorageModules"
            index_dir = self.data_dir / "index"
            t_dir = self.data_dir / "t"
            units_dir = self.data_dir / "assets/units"
            
            # Count files
            ships_found = 0
            if units_dir.exists():
                for size_dir in units_dir.glob("size_*"):
                    if size_dir.name == "size_xs":
                        continue  # Skip size_xs as per requirements
                    ships_found += len(list(size_dir.rglob("*.xml")))
            
            engine_count = len(list(engines_dir.rglob("*.xml"))) if engines_dir.exists() else 0
            storage_count = len(list(storage_dir.rglob("*.xml"))) if storage_dir.exists() else 0
            index_count = len(list(index_dir.glob("*.xml"))) if index_dir.exists() else 0
            translation_count = len(list(t_dir.glob("*.xml"))) if t_dir.exists() else 0
            
            if engine_count > 0 and ships_found > 0 and index_count > 0:
                safe_print(f"📊 Extracted:")
                safe_print(f"   - {ships_found} ship files (size_l, size_m, size_s, size_xl)")
                safe_print(f"   - {engine_count} engine files")
                safe_print(f"   - {storage_count} storage module files")
                safe_print(f"   - {index_count} index files")
                safe_print(f"   - {translation_count} translation files")
                return True
            else:
                safe_print(f"⚠️ Insufficient files extracted:")
                safe_print(f"   - Ships: {ships_found}, Engines: {engine_count}, Index: {index_count}")
                return False
                
        except subprocess.CalledProcessError as e:
            safe_print(f"❌ XRCatTool extraction failed: {e}")
            if e.stdout:
                safe_print(f"stdout: {e.stdout}")
            if e.stderr:  
                safe_print(f"stderr: {e.stderr}")
            return False
        except Exception as e:
            safe_print(f"❌ Unexpected error during extraction: {e}")
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
                
            # Copy storage modules (if they exist)
            source_storage = source_dir / "assets/props/StorageModules"
            target_storage = target_assets / "props/StorageModules"
            if source_storage.exists():
                shutil.copytree(source_storage, target_storage, dirs_exist_ok=True)
                print("✅ Copied storage module XML files")
                
            # Copy text files for ship names (language-aware)
            source_text = source_dir / "t"
            target_text = self.data_dir / "t"
            if source_text.exists():
                target_text.mkdir(exist_ok=True)
                
                # Detect language and copy appropriate file
                detected_lang_id = language_detector.get_language_id(Path(self.x4_install_path) if self.x4_install_path else None)
                lang_file = language_detector.get_language_file_name(detected_lang_id)
                lang_name = language_detector.get_language_name(detected_lang_id)
                
                preferred_text = source_text / lang_file
                if preferred_text.exists():
                    shutil.copy2(preferred_text, target_text / lang_file)
                    print(f"✅ Copied {lang_name} text file for ship names: {lang_file}")
                else:
                    # Fallback to English if preferred language not found
                    english_text = source_text / "0001-l044.xml"
                    if english_text.exists():
                        shutil.copy2(english_text, target_text / "0001-l044.xml")
                        print("⚠️ Preferred language not found - using English text file as fallback")
                    else:
                        print("❌ No text files found for ship names")
                
            return True
            
        except Exception as e:
            print(f"❌ Error copying XML files: {e}")
            return False
    
    def setup_data_directory(self) -> bool:
        """Set up the data directory with X4 files."""
        
        # First, check if we can find development data (for executable distribution)
        dev_data_path = self._find_development_data()
        if dev_data_path:
            print("🔗 Using development data files...")
            try:
                return self._copy_xml_files(dev_data_path)
            except Exception as e:
                print(f"⚠️ Could not copy from development data: {e}")
                # Continue to try X4 installation extraction
        
        # Try to find X4 installation
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