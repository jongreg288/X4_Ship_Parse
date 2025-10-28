"""
X4 Ship Parse - Standalone Launcher

This launcher handles:
1. Checking for required data files
2. Auto-detecting X4 installation if needed
3. Providing setup GUI if data is missing
4. Launching the main application
"""

import sys
import os
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def check_data_exists() -> bool:
    """Check if the required data files exist."""
    data_dir = Path("data")
    
    if not data_dir.exists():
        return False
        
    # Check for required XML files
    required_paths = [
        data_dir / "assets/props/Engines/macros",
        data_dir / "assets/units/size_l/macros",
        data_dir / "assets/units/size_m/macros", 
        data_dir / "assets/units/size_s/macros"
    ]
    
    for path in required_paths:
        if not path.exists():
            return False
        xml_files = list(path.glob("*.xml"))
        if not xml_files:
            return False
            
    return True


def launch_setup_gui():
    """Launch the setup GUI for data extraction."""
    try:
        from app.setup_gui import show_setup_dialog
        show_setup_dialog()
    except ImportError as e:
        print(f"Error importing setup GUI: {e}")
        print("Please install PyQt6: pip install PyQt6")
        return False
    except Exception as e:
        print(f"Setup GUI error: {e}")
        return False
        
    return True


def launch_main_app():
    """Launch the main application."""
    try:
        from main import main
        main()
    except ImportError as e:
        print(f"Error importing main application: {e}")
        return False
    except Exception as e:
        print(f"Application error: {e}")
        return False
        
    return True


def main():
    """Main launcher function."""
    print("🚀 X4 Ship Parse Launcher")
    print("=" * 30)
    
    # Check if data files exist
    if check_data_exists():
        print("✅ X4 data files found. Launching application...")
        launch_main_app()
    else:
        print("⚠️ X4 data files not found.")
        print("Launching setup wizard...")
        
        # Show setup GUI
        setup_success = launch_setup_gui()
        
        if setup_success and check_data_exists():
            print("✅ Setup completed. Launching application...")
            launch_main_app()
        else:
            print("❌ Setup incomplete. Please refer to README.md for manual setup.")
            input("Press Enter to exit...")


if __name__ == "__main__":
    main()