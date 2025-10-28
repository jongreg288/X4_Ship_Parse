from app.data_parser import load_ship_data, load_engine_data
from app.gui import ShipStatsApp
from app.x4_data_extractor import setup_x4_data
from PyQt6.QtWidgets import QApplication, QMessageBox
import sys
from pathlib import Path

def main():
    # Check if data directory exists, if not try to set it up
    data_dir = Path("data")
    if not data_dir.exists() or not list(data_dir.glob("**/*.xml")):
        print("🔍 X4 data not found. Attempting to locate and extract X4 game files...")
        
        success = setup_x4_data()
        if not success:
            print("\n❌ Could not automatically set up X4 data.")
            print("Please manually extract X4 XML files to the 'data' directory.")
            print("See README.md for detailed instructions.")
            
            # Still try to continue in case user has partial data
            
    engines_df = load_engine_data()  #load engines first
    ships_df = load_ship_data(engines_df=engines_df)  #pass it in

    if ships_df.empty:
        print("⚠️ No ships found — cannot launch GUI.")
        print("Make sure X4 XML files are properly extracted to the data directory.")
        return

    app = QApplication(sys.argv)
    window = ShipStatsApp(ships_df, engines_df)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
