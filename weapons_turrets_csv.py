import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, 'src')
from data_parser import get_all_data_paths, resolve_text_reference_advanced

def generate_weapons_turrets_csv():
    """Generate weapons and turrets CSV files with simplified approach."""
    
    csv_dir = Path("data/csv_cache")
    csv_dir.mkdir(exist_ok=True)
    
    weapons_data = []
    turrets_data = []
    
    # Get weapon systems paths
    weapon_systems_paths = get_all_data_paths("assets/props/WeaponSystems")
    
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
                    display_name = resolve_text_reference_advanced(name_ref) or weapon_id
                    
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
                    elif 'gatling' in weapon_lower:
                        weapon_type = 'gatling'
                    elif 'railgun' in weapon_lower:
                        weapon_type = 'railgun'
                    elif 'cannon' in weapon_lower:
                        weapon_type = 'cannon'
                    elif 'shotgun' in weapon_lower:
                        weapon_type = 'shotgun'
                    
                    # Use absolute path and then make relative
                    relative_path = str(macro_file.name)  # Just use filename to avoid path issues
                    
                    weapons_data.append({
                        'weapon_id': weapon_id,
                        'display_name': display_name,
                        'weapon_type': weapon_type,
                        'faction': faction,
                        'size_class': size_class,
                        'mk_level': int(mk),
                        'macro_file': relative_path
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
                    display_name = resolve_text_reference_advanced(name_ref) or turret_id
                    
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
                    elif 'gatling' in turret_lower:
                        turret_type = 'gatling'
                    elif 'railgun' in turret_lower:
                        turret_type = 'railgun'
                    elif 'shotgun' in turret_lower:
                        turret_type = 'shotgun'
                    elif 'arc' in turret_lower:
                        turret_type = 'arc'
                    elif 'disruptor' in turret_lower:
                        turret_type = 'disruptor'
                    
                    # Use absolute path and then make relative
                    relative_path = str(macro_file.name)  # Just use filename to avoid path issues
                    
                    turrets_data.append({
                        'turret_id': turret_id,
                        'display_name': display_name,
                        'turret_type': turret_type,
                        'faction': faction,
                        'size_class': size_class,
                        'mk_level': int(mk),
                        'macro_file': relative_path
                    })
                
            except Exception as e:
                print(f"⚠️ Error processing {macro_file.name}: {e}")
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
    
    return len(weapons_data), len(turrets_data)

if __name__ == "__main__":
    print("🚀 Generating Weapons and Turrets CSV files...")
    weapons_count, turrets_count = generate_weapons_turrets_csv()
    print(f"📊 Summary: {weapons_count} weapons, {turrets_count} turrets")