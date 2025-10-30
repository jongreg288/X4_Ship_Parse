#!/usr/bin/env python3
"""
Temporary Ship Comparison Table Generator
Extracts and compares jerk and physics data from ship macro files
Organized by macro class and ship type as requested
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
from collections import defaultdict

def extract_ship_data():
    """Extract jerk and physics data from all ship macro files."""
    units_dir = Path("data/assets/units")
    ships_data = []
    
    if not units_dir.exists():
        print(f"❌ Units directory not found: {units_dir}")
        return pd.DataFrame()
    
    # Find all ship macro files
    ship_files = []
    for size_dir in units_dir.glob("size_*"):
        macros_dir = size_dir / "macros"
        if macros_dir.exists():
            ship_files.extend(macros_dir.glob("ship_*.xml"))
    
    print(f"🔍 Found {len(ship_files)} ship macro files")
    
    for ship_file in ship_files:
        try:
            tree = ET.parse(ship_file)
            root = tree.getroot()
            
            # Find macro element with class starting with "ship" but exclude ship_xs
            macro_elem = None
            for macro in root.findall(".//macro"):
                macro_class = macro.get("class", "")
                if macro_class.startswith("ship") and not macro_class.startswith("ship_xs"):
                    macro_elem = macro
                    break
            
            if macro_elem is None:
                continue
                
            macro_name = macro_elem.get("name", "")
            macro_class = macro_elem.get("class", "")
            
            if not macro_name:
                continue
            
            # Extract ship type
            ship_elem = macro_elem.find(".//ship")
            ship_type = ship_elem.get("type", "unknown") if ship_elem is not None else "unknown"
            
            # Extract identification info
            identification = macro_elem.find(".//identification")
            maker_race = identification.get("makerrace", "") if identification is not None else ""
            
            # Extract jerk parameters (lines 18-24 reference)
            jerk_elem = macro_elem.find(".//jerk")
            jerk_data = {}
            if jerk_elem is not None:
                # Forward jerk
                forward = jerk_elem.find("forward")
                if forward is not None:
                    jerk_data["forward_accel"] = float(forward.get("accel", "0"))
                    jerk_data["forward_decel"] = float(forward.get("decel", "0"))
                    jerk_data["forward_ratio"] = float(forward.get("ratio", "0"))
                
                # Forward boost jerk
                forward_boost = jerk_elem.find("forward_boost")
                if forward_boost is not None:
                    jerk_data["boost_accel"] = float(forward_boost.get("accel", "0"))
                    jerk_data["boost_ratio"] = float(forward_boost.get("ratio", "0"))
                
                # Forward travel jerk
                forward_travel = jerk_elem.find("forward_travel")
                if forward_travel is not None:
                    jerk_data["travel_accel"] = float(forward_travel.get("accel", "0"))
                    jerk_data["travel_decel"] = float(forward_travel.get("decel", "0"))
                    jerk_data["travel_ratio"] = float(forward_travel.get("ratio", "0"))
                
                # Strafe and angular
                strafe = jerk_elem.find("strafe")
                if strafe is not None:
                    jerk_data["strafe"] = float(strafe.get("value", "0"))
                
                angular = jerk_elem.find("angular")
                if angular is not None:
                    jerk_data["angular"] = float(angular.get("value", "0"))
            
            # Extract physics parameters (lines 43-46 reference)
            physics_elem = macro_elem.find(".//physics")
            physics_data = {}
            if physics_elem is not None:
                physics_data["mass"] = float(physics_elem.get("mass", "0"))
                
                # Inertia
                inertia = physics_elem.find("inertia")
                if inertia is not None:
                    physics_data["inertia_pitch"] = float(inertia.get("pitch", "0"))
                    physics_data["inertia_yaw"] = float(inertia.get("yaw", "0"))
                    physics_data["inertia_roll"] = float(inertia.get("roll", "0"))
                
                # Drag
                drag = physics_elem.find("drag")
                if drag is not None:
                    physics_data["drag_forward"] = float(drag.get("forward", "0"))
                    physics_data["drag_reverse"] = float(drag.get("reverse", "0"))
                    physics_data["drag_horizontal"] = float(drag.get("horizontal", "0"))
                    physics_data["drag_vertical"] = float(drag.get("vertical", "0"))
                    physics_data["drag_pitch"] = float(drag.get("pitch", "0"))
                    physics_data["drag_yaw"] = float(drag.get("yaw", "0"))
                    physics_data["drag_roll"] = float(drag.get("roll", "0"))
                
                # Acceleration factors
                accfactors = physics_elem.find("accfactors")
                if accfactors is not None:
                    physics_data["accfactor_forward"] = float(accfactors.get("forward", "1.0"))
            
            # Extract hull max for reference
            hull_elem = macro_elem.find(".//hull")
            hull_max = int(hull_elem.get("max", "0")) if hull_elem is not None else 0
            
            # Combine all data
            ship_data = {
                "macro_name": macro_name,
                "macro_class": macro_class,
                "ship_type": ship_type,
                "maker_race": maker_race,
                "hull_max": hull_max,
                **jerk_data,
                **physics_data
            }
            
            ships_data.append(ship_data)
            
        except ET.ParseError as e:
            print(f"❌ Error parsing {ship_file}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error parsing {ship_file}: {e}")
    
    df = pd.DataFrame(ships_data)
    print(f"✅ Extracted data from {len(df)} ships")
    return df

def generate_comparison_tables(df):
    """Generate comparison tables organized by macro class and ship type."""
    if df.empty:
        print("❌ No data to generate tables")
        return
    
    print("\n" + "="*80)
    print("🚀 SHIP COMPARISON TABLES")
    print("="*80)
    
    # Group by macro class first
    macro_classes = sorted(df['macro_class'].unique())
    
    for i, macro_class in enumerate(macro_classes):
        # Add line break between macro classes (except for the first one)
        if i > 0:
            print("\n<br/>")
            
        class_df = df[df['macro_class'] == macro_class]
        
        print(f"\n{'🔧 MACRO CLASS: ' + macro_class.upper():<80}")
        print("-" * 80)
        
        # Group by ship type within each macro class and sort ships by name
        ship_types = sorted(class_df['ship_type'].unique())
        
        for ship_type in ship_types:
            type_df = class_df[class_df['ship_type'] == ship_type].sort_values('macro_name')
            
            print(f"\n⚔️  Ship Type: {ship_type.upper()}")
            print(f"   Ships in this category: {len(type_df)}")
            
            # Display key jerk parameters table
            jerk_columns = ['macro_name', 'maker_race', 'hull_max', 
                           'forward_accel', 'forward_decel', 'boost_accel', 
                           'travel_accel', 'strafe', 'angular']
            
            if all(col in type_df.columns for col in jerk_columns):
                print(f"\n   📊 JERK PARAMETERS:")
                jerk_table = type_df[jerk_columns].copy()
                jerk_table['macro_name'] = jerk_table['macro_name'].str.replace('_macro', '')
                
                # Format for better display
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', 25)
                
                print(jerk_table.to_string(index=False))
            
            # Display key physics parameters table
            physics_columns = ['macro_name', 'mass', 'inertia_pitch', 'inertia_yaw', 
                             'drag_forward', 'drag_reverse', 'accfactor_forward']
            
            if all(col in type_df.columns for col in physics_columns):
                print(f"\n   ⚙️  PHYSICS PARAMETERS:")
                physics_table = type_df[physics_columns].copy()
                physics_table['macro_name'] = physics_table['macro_name'].str.replace('_macro', '')
                
                print(physics_table.to_string(index=False))
            
            print("-" * 60)

def main():
    """Main function to run the comparison table generator."""
    print("🔍 X4 Ship Comparison Table Generator")
    print("📊 Extracting jerk and physics data from ship macros...")
    
    # Extract ship data
    df = extract_ship_data()
    
    if df.empty:
        print("❌ No ship data found. Make sure the data directory exists.")
        return
    
    # Generate comparison tables
    generate_comparison_tables(df)
    
    # Summary statistics
    print(f"\n{'📈 SUMMARY STATISTICS':<80}")
    print("=" * 80)
    print(f"Total ships analyzed: {len(df)}")
    print(f"Macro classes found: {len(df['macro_class'].unique())}")
    print(f"Ship types found: {len(df['ship_type'].unique())}")
    print(f"Factions found: {len(df['maker_race'].unique())}")
    
    print(f"\nMacro classes: {', '.join(sorted(df['macro_class'].unique()))}")
    print(f"Ship types: {', '.join(sorted(df['ship_type'].unique()))}")
    print(f"Factions: {', '.join(sorted(df['maker_race'].unique()))}")
    
    # Export to CSV for further analysis
    output_file = Path("src/tests/ship_comparison_data.csv")
    df.to_csv(output_file, index=False)
    print(f"\n💾 Raw data exported to: {output_file}")

if __name__ == "__main__":
    main()