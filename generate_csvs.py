#!/usr/bin/env python3
"""
Standalone CSV Generation Script

This script generates optimized CSV files for X4 Ship Matrix:
- weapons.csv: All weapon data from WeaponSystems
- turrets.csv: All turret data from WeaponSystems  
- ships.csv: All ship data
- engines.csv: All engine data
- shields.csv: All shield data

These CSV files are placed in the optimal location for packaging.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

# Now import the modules
try:
    from data_parser import generate_all_csv_files
except ImportError:
    # Handle relative import issues
    import importlib.util
    
    # Load data_parser module manually
    data_parser_path = src_dir / "data_parser.py"
    spec = importlib.util.spec_from_file_location("data_parser", data_parser_path)
    data_parser = importlib.util.module_from_spec(spec)
    
    # Also need to load language_detector
    lang_detector_path = src_dir / "language_detector.py"
    lang_spec = importlib.util.spec_from_file_location("language_detector", lang_detector_path)
    lang_detector = importlib.util.module_from_spec(lang_spec)
    sys.modules['language_detector'] = lang_detector
    lang_spec.loader.exec_module(lang_detector)
    
    # Add to sys.modules to resolve relative imports
    sys.modules['data_parser'] = data_parser
    spec.loader.exec_module(data_parser)
    
    generate_all_csv_files = data_parser.generate_all_csv_files

def determine_best_csv_location():
    """Determine the best location for CSV files for packaging."""
    
    # Option 1: Inside src/ for easy import by the application
    src_location = Path("src/csv_data")
    
    # Option 2: In data/ alongside the XML data  
    data_location = Path("data/csv_cache")
    
    # Option 3: In a dedicated assets folder for packaging
    assets_location = Path("assets/csv_data")
    
    # For an executable package, we want CSV files in the same directory as the executable
    # or in a subdirectory that gets packaged with the .exe
    
    print("📍 Available CSV locations:")
    print(f"  1. {src_location} - Inside source code (for development)")
    print(f"  2. {data_location} - With game data (current choice)")  
    print(f"  3. {assets_location} - Dedicated assets folder (for packaging)")
    
    # For this project, data/csv_cache is best because:
    # 1. It keeps CSV files with the game data they're derived from
    # 2. Easy to package with the executable 
    # 3. Can be gitignored or included as needed
    
    return data_location

def main():
    """Main CSV generation function."""
    print("🚀 X4 Ship Matrix CSV Generator")
    print("=" * 50)
    
    # Determine CSV output location
    csv_location = determine_best_csv_location()
    print(f"📁 CSV files will be saved to: {csv_location}")
    
    # Create the directory
    csv_location.mkdir(parents=True, exist_ok=True)
    
    # Generate all CSV files
    try:
        results = generate_all_csv_files()
        
        print("\n📊 Generation Results:")
        print(f"  Ships: {results['ships']}")
        print(f"  Engines: {results['engines']}")
        print(f"  Shields: {results['shields']}")
        print(f"  Weapons: {results['weapons']}")
        print(f"  Turrets: {results['turrets']}")
        
        total_items = sum(results.values())
        print(f"\n✅ Successfully generated CSV files with {total_items} total items")
        
        # List the generated files
        csv_files = list(csv_location.glob("*.csv"))
        if csv_files:
            print(f"\n📄 Generated CSV files:")
            for csv_file in sorted(csv_files):
                size_mb = csv_file.stat().st_size / (1024 * 1024)
                print(f"  {csv_file.name} ({size_mb:.2f} MB)")
        
        # Packaging recommendations
        print(f"\n📦 Packaging Recommendations:")
        print(f"  • Include the entire '{csv_location}' folder in your .exe package")
        print(f"  • CSV files provide 10-100x faster loading than XML parsing")
        print(f"  • Total CSV size: ~{sum(f.stat().st_size for f in csv_files) / (1024*1024):.1f}MB (vs several GB of XML)")
        print(f"  • Update CSVs whenever X4 game data changes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during CSV generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 CSV generation completed successfully!")
        print("You can now use the fast CSV loading in your Ship Matrix application.")
    else:
        print("\n💥 CSV generation failed. Check error messages above.")
        sys.exit(1)