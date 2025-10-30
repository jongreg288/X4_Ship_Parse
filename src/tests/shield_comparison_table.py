#!/usr/bin/env python3
"""
X4 Shield Comparison Table Generator
Extracts shield data from X4 shield macro files and creates a CSV table.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import xml.etree.ElementTree as ET

def resolve_text_reference_basic(ref):
    """Basic text reference resolver - just return the reference for now."""
    return ref

def parse_shields():
    """Parse shield data from X4 shield macro files."""
    shield_dir = Path("data/assets/props/SurfaceElements/macros")
    shields = []
    
    if not shield_dir.exists():
        print(f"Shield directory not found: {shield_dir}")
        return pd.DataFrame()
    
    # Find all shield macro files
    shield_files = list(shield_dir.glob("shield_*.xml"))
    
    for shield_file in shield_files:
        try:
            tree = ET.parse(shield_file)
            root = tree.getroot()
            
            # Find macro element with class="shieldgenerator"
            macro_elem = root.find(".//macro[@class='shieldgenerator']")
            if macro_elem is None:
                continue
                
            macro_name = macro_elem.get("name", "")
            if not macro_name:
                continue
            
            # Extract identification properties
            identification = macro_elem.find(".//identification")
            name_ref = identification.get("name", "") if identification is not None else ""
            basename_ref = identification.get("basename", "") if identification is not None else ""
            shortname_ref = identification.get("shortname", "") if identification is not None else ""
            description_ref = identification.get("description", "") if identification is not None else ""
            maker_race = identification.get("makerrace", "") if identification is not None else ""
            mk = identification.get("mk", "") if identification is not None else ""
            
            # Extract shield properties - line 8 reference: <recharge max="5147" rate="26" delay="0.5" />
            recharge_elem = macro_elem.find(".//recharge")
            recharge_max = 0
            recharge_rate = 0
            recharge_delay = 0
            if recharge_elem is not None:
                recharge_max = int(recharge_elem.get("max", "0"))
                recharge_rate = int(recharge_elem.get("rate", "0"))
                recharge_delay = float(recharge_elem.get("delay", "0"))
            
            # Extract hull properties (shield module hull)
            hull_elem = macro_elem.find(".//hull")
            hull_max = 0
            hull_threshold = 0
            if hull_elem is not None:
                hull_max = int(hull_elem.get("max", "0"))
                hull_threshold = float(hull_elem.get("threshold", "0"))
            
            # Determine shield size from macro name
            shield_size = None
            macro_lower = macro_name.lower()
            if "_s_" in macro_lower:
                shield_size = "s"
            elif "_m_" in macro_lower:
                shield_size = "m"
            elif "_l_" in macro_lower:
                shield_size = "l"
            elif "_xl_" in macro_lower:
                shield_size = "xl"
                
            # Create display name from macro name
            display_name = macro_name.replace("_macro", "").replace("_", " ").title()
            if mk:
                display_name = f"{display_name} Mk{mk}"
            
            shields.append({
                "name": macro_name,
                "display_name": display_name,
                "basename_ref": basename_ref,
                "name_ref": name_ref,
                "shortname_ref": shortname_ref,
                "description_ref": description_ref,
                "maker_race": maker_race,
                "mk": mk,
                "shield_size": shield_size,
                "recharge_max": recharge_max,
                "recharge_rate": recharge_rate,
                "recharge_delay": recharge_delay,
                "hull_max": hull_max,
                "hull_threshold": hull_threshold
            })
            
        except ET.ParseError as e:
            print(f"Error parsing {shield_file}: {e}")
        except Exception as e:
            print(f"Unexpected error parsing {shield_file}: {e}")
    
    df = pd.DataFrame(shields)
    print(f"Loaded {len(df)} shields from {shield_dir}")
    return df

def generate_shield_csv():
    """Generate a CSV table of all shield data."""
    print("🛡️  X4 Shield Comparison Table Generator")
    print("📊 Extracting shield data from macro files...")
    
    # Parse shield data using existing function
    shields_df = parse_shields()
    
    if shields_df.empty:
        print("❌ No shield data found. Make sure the data directory exists.")
        return
    
    print(f"✅ Extracted data from {len(shields_df)} shields")
    
    # Display summary statistics
    print(f"\n{'📈 SHIELD SUMMARY STATISTICS':<80}")
    print("=" * 80)
    print(f"Total shields analyzed: {len(shields_df)}")
    print(f"Shield sizes found: {', '.join(sorted(shields_df['shield_size'].dropna().unique()))}")
    print(f"Manufacturer races: {', '.join(sorted(shields_df['maker_race'].dropna().unique()))}")
    print(f"Mark levels: {', '.join(sorted(shields_df['mk'].dropna().unique()))}")
    
    # Show recharge range statistics
    if not shields_df['recharge_max'].empty:
        recharge_stats = shields_df['recharge_max'].describe()
        print(f"\nRecharge Max Statistics:")
        print(f"  Min: {recharge_stats['min']:,.0f}")
        print(f"  Max: {recharge_stats['max']:,.0f}")
        print(f"  Mean: {recharge_stats['mean']:,.0f}")
        print(f"  Median: {recharge_stats['50%']:,.0f}")
    
    # Display top shields by recharge capacity
    print(f"\n{'🏆 TOP 10 SHIELDS BY RECHARGE CAPACITY':<80}")
    print("-" * 80)
    top_shields = shields_df.nlargest(10, 'recharge_max')[
        ['display_name', 'maker_race', 'shield_size', 'recharge_max', 'recharge_rate', 'mk']
    ]
    print(top_shields.to_string(index=False))
    
    # Display shields grouped by size
    print(f"\n{'🔍 SHIELDS BY SIZE CLASS':<80}")
    print("=" * 80)
    
    for size in sorted(shields_df['shield_size'].dropna().unique()):
        size_shields = shields_df[shields_df['shield_size'] == size].sort_values('recharge_max', ascending=False)
        
        print(f"\n🛡️  Size Class: {size.upper()}")
        print(f"   Shields in this category: {len(size_shields)}")
        
        # Show key shield parameters
        display_cols = ['display_name', 'maker_race', 'mk', 'recharge_max', 'recharge_rate', 'recharge_delay', 'hull_max']
        size_display = size_shields[display_cols].copy()
        
        print(f"\n   📊 SHIELD PARAMETERS:")
        print(size_display.to_string(index=False))
        print("-" * 60)
    
    # Export to CSV
    output_file = Path("src/tests/shield_comparison_data.csv")
    
    # Select and order columns for CSV export
    csv_columns = [
        'display_name',         # Human-readable name  
        'maker_race',           # Manufacturer
        'shield_size',          # Size class (s, m, l, xl)
        'recharge_max',         # Maximum shield capacity
        'recharge_rate',        # Recharge rate per second
        'recharge_delay',       # Delay before recharge starts
        'hull_max',             # Shield module hull points
        'hull_threshold',       # Hull damage threshold
    ]
    
    # Ensure all columns exist, add missing ones with default values
    for col in csv_columns:
        if col not in shields_df.columns:
            shields_df[col] = ""
    
    # Sort by size class, then by recharge capacity
    shields_df_sorted = shields_df.sort_values(['shield_size', 'recharge_max'], ascending=[True, False])
    
    # Export to CSV
    shields_df_sorted[csv_columns].to_csv(output_file, index=False)
    print(f"\n💾 Shield data exported to: {output_file}")
    
    # Show sample of exported data
    print(f"\n{'📋 SAMPLE OF EXPORTED DATA':<80}")
    print("-" * 80)
    sample_cols = ['name', 'display_name', 'maker_race', 'shield_size', 'recharge_max', 'recharge_rate']
    print(shields_df_sorted[sample_cols].head(10).to_string(index=False))

def main():
    """Main function to run the shield comparison table generator."""
    try:
        generate_shield_csv()
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error generating shield comparison table: {e}")
        raise

if __name__ == "__main__":
    main()