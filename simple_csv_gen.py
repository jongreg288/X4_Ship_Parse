#!/usr/bin/env python3
"""
Simple CSV Generation Script

Generates CSV files by importing as a package.
"""

if __name__ == "__main__":
    print("🚀 X4 Ship Matrix CSV Generator")
    print("=" * 50)
    
    # Import and run generation
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, 'src')
        
        # Create CSV output directory
        csv_dir = Path("data/csv_cache")
        csv_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 CSV files will be saved to: {csv_dir}")
        
        # Run manual generation with proper imports
        import pandas as pd
        import xml.etree.ElementTree as ET  
        
        # Load the necessary modules
        from language_detector import language_detector
        import data_parser
        
        print("📊 Loading text mappings...")
        data_parser.load_text_mappings()
        
        print("📊 Generating engines.csv...")
        engines_df = data_parser.load_engine_data()
        if not engines_df.empty:
            engines_csv = csv_dir / "engines.csv"
            engines_df.to_csv(engines_csv, index=False)
            print(f"✅ Saved {len(engines_df)} engines to {engines_csv}")
        
        print("📊 Generating ships.csv...")
        ships_df = data_parser.load_ship_data(engines_df)
        if not ships_df.empty:
            ships_csv = csv_dir / "ships.csv"
            ships_df.to_csv(ships_csv, index=False)
            print(f"✅ Saved {len(ships_df)} ships to {ships_csv}")
        
        print("📊 Generating shields.csv...")
        shields_df = data_parser.parse_shields()
        if not shields_df.empty:
            shields_csv = csv_dir / "shields.csv"
            shields_df.to_csv(shields_csv, index=False)
            print(f"✅ Saved {len(shields_df)} shields to {shields_csv}")
        
        # For now, let's manually create weapon/turret CSVs with basic data
        print("📊 Generating basic weapons.csv and turrets.csv...")
        
        # Create basic weapon DataFrame structure
        weapons_data = []
        turrets_data = []
        
        # Scan WeaponSystems directories
        weapon_systems_paths = data_parser.get_all_data_paths("assets/props/WeaponSystems")
        
        for weapon_systems_path in weapon_systems_paths:
            if not weapon_systems_path.exists():
                continue
                
            print(f"Scanning: {weapon_systems_path}")
            
            # Find all macro files
            for macro_file in weapon_systems_path.rglob("*_macro.xml"):
                try:
                    tree = ET.parse(macro_file)
                    root = tree.getroot()
                    
                    # Check for weapon macros
                    weapon_macro = root.find('macro[@class="weapon"]')
                    if weapon_macro is not None:
                        weapon_id = weapon_macro.get('name', '')
                        
                        # Extract basic weapon data
                        identification = weapon_macro.find('.//identification')
                        name_ref = identification.get('name', '') if identification is not None else ''
                        mk = identification.get('mk', '1') if identification is not None else '1'
                        
                        # Get display name
                        display_name = data_parser.resolve_text_reference_advanced(name_ref) or weapon_id
                        
                        # Extract faction and size
                        faction = 'unknown'
                        size_class = 'unknown'
                        weapon_type = 'unknown'
                        
                        weapon_lower = weapon_id.lower()
                        
                        # Extract faction
                        faction_map = {
                            'arg': 'argon', 'par': 'paranid', 'tel': 'teladi', 'spl': 'split',
                            'ter': 'terran', 'kha': 'khaak', 'xen': 'xenon', 'bor': 'boron', 'gen': 'generic'
                        }
                        for prefix, f in faction_map.items():
                            if f'_{prefix}_' in weapon_lower:
                                faction = f
                                break
                        
                        # Extract size
                        if '_s_' in weapon_lower:
                            size_class = 'small'
                        elif '_m_' in weapon_lower:
                            size_class = 'medium'
                        elif '_l_' in weapon_lower:
                            size_class = 'large'
                        elif '_xl_' in weapon_lower:
                            size_class = 'extra_large'
                        
                        # Extract weapon type
                        if 'beam' in weapon_lower or 'laser' in weapon_lower:
                            weapon_type = 'beam'
                        elif 'plasma' in weapon_lower:
                            weapon_type = 'plasma'
                        elif 'ion' in weapon_lower:
                            weapon_type = 'particle'
                        elif 'pulse' in weapon_lower or 'burst' in weapon_lower:
                            weapon_type = 'pulse'
                        elif 'mining' in weapon_lower:
                            weapon_type = 'mining'
                        
                        weapons_data.append({
                            'weapon_id': weapon_id,
                            'display_name': display_name,
                            'weapon_type': weapon_type,
                            'faction': faction,
                            'size_class': size_class,
                            'mk_level': int(mk),
                            'macro_file': str(macro_file.relative_to(Path.cwd()))
                        })
                    
                    # Check for turret macros
                    turret_macro = root.find('macro[@class="turret"]')
                    if turret_macro is not None:
                        turret_id = turret_macro.get('name', '')
                        
                        # Extract basic turret data
                        identification = turret_macro.find('.//identification')
                        name_ref = identification.get('name', '') if identification is not None else ''
                        mk = identification.get('mk', '1') if identification is not None else '1'
                        makerrace = identification.get('makerrace', '') if identification is not None else ''
                        
                        # Get display name
                        display_name = data_parser.resolve_text_reference_advanced(name_ref) or turret_id
                        
                        # Extract faction and size
                        faction = makerrace or 'unknown'
                        size_class = 'unknown'
                        turret_type = 'unknown'
                        
                        turret_lower = turret_id.lower()
                        
                        # Extract faction if not from makerrace
                        if faction == 'unknown':
                            faction_map = {
                                'arg': 'argon', 'par': 'paranid', 'tel': 'teladi', 'spl': 'split',
                                'ter': 'terran', 'kha': 'khaak', 'xen': 'xenon', 'bor': 'boron', 'gen': 'generic'
                            }
                            for prefix, f in faction_map.items():
                                if f'_{prefix}_' in turret_lower:
                                    faction = f
                                    break
                        
                        # Extract size
                        if '_s_' in turret_lower:
                            size_class = 'small'
                        elif '_m_' in turret_lower:
                            size_class = 'medium'
                        elif '_l_' in turret_lower:
                            size_class = 'large'
                        elif '_xl_' in turret_lower:
                            size_class = 'extra_large'
                        
                        # Extract turret type
                        if 'beam' in turret_lower or 'laser' in turret_lower:
                            turret_type = 'beam'
                        elif 'plasma' in turret_lower:
                            turret_type = 'plasma'
                        elif 'ion' in turret_lower:
                            turret_type = 'particle'
                        elif 'pulse' in turret_lower or 'burst' in turret_lower:
                            turret_type = 'pulse'
                        elif 'mining' in turret_lower:
                            turret_type = 'mining'
                        elif 'flak' in turret_lower:
                            turret_type = 'flak'
                        
                        turrets_data.append({
                            'turret_id': turret_id,
                            'display_name': display_name,
                            'turret_type': turret_type,
                            'faction': faction,
                            'size_class': size_class,
                            'mk_level': int(mk),
                            'macro_file': str(macro_file.relative_to(Path.cwd()))
                        })
                    
                except Exception as e:
                    print(f"⚠️ Error processing {macro_file}: {e}")
                    continue
        
        # Save weapons and turrets CSVs
        if weapons_data:
            weapons_df = pd.DataFrame(weapons_data)
            weapons_df = weapons_df.sort_values(['faction', 'size_class', 'weapon_type', 'mk_level'])
            weapons_csv = csv_dir / "weapons.csv"
            weapons_df.to_csv(weapons_csv, index=False)
            print(f"✅ Saved {len(weapons_df)} weapons to {weapons_csv}")
        
        if turrets_data:
            turrets_df = pd.DataFrame(turrets_data)
            turrets_df = turrets_df.sort_values(['faction', 'size_class', 'turret_type', 'mk_level'])
            turrets_csv = csv_dir / "turrets.csv"
            turrets_df.to_csv(turrets_csv, index=False)
            print(f"✅ Saved {len(turrets_df)} turrets to {turrets_csv}")
        
        # Summary
        print(f"\n📊 Generation Results:")
        print(f"  Ships: {len(ships_df) if not ships_df.empty else 0}")
        print(f"  Engines: {len(engines_df) if not engines_df.empty else 0}")
        print(f"  Shields: {len(shields_df) if not shields_df.empty else 0}")
        print(f"  Weapons: {len(weapons_data)}")
        print(f"  Turrets: {len(turrets_data)}")
        
        # List generated files
        csv_files = list(csv_dir.glob("*.csv"))
        if csv_files:
            print(f"\n📄 Generated CSV files:")
            for csv_file in sorted(csv_files):
                size_mb = csv_file.stat().st_size / (1024 * 1024)
                print(f"  {csv_file.name} ({size_mb:.2f} MB)")
        
        print(f"\n✅ CSV generation completed successfully!")
        print(f"📦 For .exe packaging, include the entire '{csv_dir}' folder")
        
    except Exception as e:
        print(f"❌ Error during CSV generation: {e}")
        import traceback
        traceback.print_exc()