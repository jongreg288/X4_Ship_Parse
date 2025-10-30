#!/usr/bin/env python3
"""
CSV Generator for X4 Weapons and Turrets

This script parses X4 weapon and turret data from XML files and generates
optimized CSV files for fast loading in the Ship Matrix application.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
try:
    from .data_parser import get_all_data_paths, TEXT_MAPPINGS, load_text_mappings
except ImportError:
    # Handle case when run as standalone script
    import sys
    sys.path.append('.')
    from src.data_parser import get_all_data_paths, TEXT_MAPPINGS, load_text_mappings

class WeaponCSVGenerator:
    def __init__(self):
        self.weapons_data = []
        self.turrets_data = []
        self.weapon_systems_paths = []
        
        # Find all WeaponSystems directories
        for path in get_all_data_paths("assets/props/WeaponSystems"):
            self.weapon_systems_paths.append(path)
            print(f"Found WeaponSystems directory: {path}")
    
    def extract_faction_from_name(self, name: str) -> str:
        """Extract faction from weapon/turret name."""
        # Common faction prefixes in X4
        faction_map = {
            'arg': 'argon',
            'par': 'paranid', 
            'tel': 'teladi',
            'spl': 'split',
            'ter': 'terran',
            'kha': 'khaak',
            'xen': 'xenon',
            'bor': 'boron',
            'gen': 'generic',
            'yak': 'yakuza',
            'pio': 'pioneer'
        }
        
        for prefix, faction in faction_map.items():
            if f'_{prefix}_' in name.lower():
                return faction
        
        return 'unknown'
    
    def extract_size_class(self, name: str) -> str:
        """Extract size class from weapon/turret name."""
        size_patterns = {
            '_xs_': 'extra_small',
            '_s_': 'small', 
            '_m_': 'medium',
            '_l_': 'large',
            '_xl_': 'extra_large'
        }
        
        name_lower = name.lower()
        for pattern, size in size_patterns.items():
            if pattern in name_lower:
                return size
        
        return 'unknown'
    
    def extract_mk_level(self, name: str) -> int:
        """Extract Mk level from weapon/turret name."""
        match = re.search(r'_mk(\d+)', name.lower())
        return int(match.group(1)) if match else 1
    
    def get_text_value(self, text_ref: str) -> str:
        """Get localized text value from reference."""
        if not text_ref or not TEXT_MAPPINGS:
            return text_ref or ''
        
        # Handle format like "{20105,2084}"
        if text_ref.startswith('{') and text_ref.endswith('}'):
            text_ref = text_ref[1:-1]
        
        return TEXT_MAPPINGS.get(text_ref, text_ref)
    
    def parse_weapon_macro(self, macro_path: Path) -> Optional[Dict]:
        """Parse a weapon macro file to extract weapon data."""
        try:
            tree = ET.parse(macro_path)
            root = tree.getroot()
            
            macro_elem = root.find('macro[@class="weapon"]')
            if macro_elem is None:
                return None
            
            weapon_id = macro_elem.get('name', '')
            properties = macro_elem.find('properties')
            
            if properties is None:
                return None
            
            # Extract identification data
            identification = properties.find('identification')
            name_ref = identification.get('name', '') if identification is not None else ''
            basename_ref = identification.get('basename', '') if identification is not None else ''
            description_ref = identification.get('description', '') if identification is not None else ''
            mk_level = int(identification.get('mk', '1')) if identification is not None else 1
            
            # Get localized text
            display_name = self.get_text_value(name_ref) or weapon_id
            basename = self.get_text_value(basename_ref) or ''
            description = self.get_text_value(description_ref) or ''
            
            # Extract weapon stats
            bullet_elem = properties.find('bullet')
            bullet_class = bullet_elem.get('class', '') if bullet_elem is not None else ''
            
            heat_elem = properties.find('heat')
            overheat = float(heat_elem.get('overheat', '0')) if heat_elem is not None else 0
            cooldelay = float(heat_elem.get('cooldelay', '0')) if heat_elem is not None else 0
            coolrate = float(heat_elem.get('coolrate', '0')) if heat_elem is not None else 0
            
            rotation_elem = properties.find('rotationspeed')
            max_rotation = float(rotation_elem.get('max', '0')) if rotation_elem is not None else 0
            
            hull_elem = properties.find('hull')
            max_hull = float(hull_elem.get('max', '0')) if hull_elem is not None else 0
            
            # Extract derived data
            faction = self.extract_faction_from_name(weapon_id)
            size_class = self.extract_size_class(weapon_id)
            
            # Determine weapon type from name patterns
            weapon_type = self.classify_weapon_type(weapon_id)
            
            weapon_data = {
                'weapon_id': weapon_id,
                'display_name': display_name,
                'basename': basename,
                'description': description,
                'weapon_type': weapon_type,
                'faction': faction,
                'size_class': size_class,
                'mk_level': mk_level,
                'bullet_class': bullet_class,
                'overheat_threshold': overheat,
                'cooling_delay': cooldelay,
                'cooling_rate': coolrate,
                'max_rotation_speed': max_rotation,
                'hull_points': max_hull,
                'macro_file': str(macro_path.relative_to(macro_path.parents[5]))  # Relative to project root
            }
            
            return weapon_data
            
        except Exception as e:
            print(f"Error parsing weapon macro {macro_path}: {e}")
            return None
    
    def parse_turret_macro(self, macro_path: Path) -> Optional[Dict]:
        """Parse a turret macro file to extract turret data."""
        try:
            tree = ET.parse(macro_path)
            root = tree.getroot()
            
            macro_elem = root.find('macro[@class="turret"]')
            if macro_elem is None:
                return None
            
            turret_id = macro_elem.get('name', '')
            properties = macro_elem.find('properties')
            
            if properties is None:
                return None
            
            # Extract identification data
            identification = properties.find('identification')
            name_ref = identification.get('name', '') if identification is not None else ''
            basename_ref = identification.get('basename', '') if identification is not None else ''
            description_ref = identification.get('description', '') if identification is not None else ''
            mk_level = int(identification.get('mk', '1')) if identification is not None else 1
            makerrace = identification.get('makerrace', '') if identification is not None else ''
            
            # Get localized text
            display_name = self.get_text_value(name_ref) or turret_id
            basename = self.get_text_value(basename_ref) or ''
            description = self.get_text_value(description_ref) or ''
            
            # Extract turret stats
            bullet_elem = properties.find('bullet')
            bullet_class = bullet_elem.get('class', '') if bullet_elem is not None else ''
            
            rotation_elem = properties.find('rotationspeed')
            max_rotation = float(rotation_elem.get('max', '0')) if rotation_elem is not None else 0
            
            rotation_accel_elem = properties.find('rotationacceleration')
            max_rotation_accel = float(rotation_accel_elem.get('max', '0')) if rotation_accel_elem is not None else 0
            
            reload_elem = properties.find('reload')
            reload_rate = float(reload_elem.get('rate', '0')) if reload_elem is not None else 0
            reload_time = float(reload_elem.get('time', '0')) if reload_elem is not None else 0
            
            hull_elem = properties.find('hull')
            hull_threshold = float(hull_elem.get('threshold', '0')) if hull_elem is not None else 0
            hull_integrated = hull_elem.get('integrated', '0') == '1' if hull_elem is not None else False
            
            # Extract derived data
            faction = makerrace if makerrace else self.extract_faction_from_name(turret_id)
            size_class = self.extract_size_class(turret_id)
            
            # Determine turret type from name patterns
            turret_type = self.classify_turret_type(turret_id)
            
            turret_data = {
                'turret_id': turret_id,
                'display_name': display_name,
                'basename': basename,
                'description': description,
                'turret_type': turret_type,
                'faction': faction,
                'size_class': size_class,
                'mk_level': mk_level,
                'bullet_class': bullet_class,
                'max_rotation_speed': max_rotation,
                'max_rotation_acceleration': max_rotation_accel,
                'reload_rate': reload_rate,
                'reload_time': reload_time,
                'hull_threshold': hull_threshold,
                'hull_integrated': hull_integrated,
                'macro_file': str(macro_path.relative_to(macro_path.parents[5]))  # Relative to project root
            }
            
            return turret_data
            
        except Exception as e:
            print(f"Error parsing turret macro {macro_path}: {e}")
            return None
    
    def classify_weapon_type(self, weapon_id: str) -> str:
        """Classify weapon type based on name patterns."""
        weapon_id_lower = weapon_id.lower()
        
        type_patterns = {
            'beam': ['beam', 'laser'],
            'plasma': ['plasma'],
            'particle': ['particle', 'ion'],
            'pulse': ['pulse', 'burst'],
            'mining': ['mining'],
            'missile': ['missile'],
            'torpedo': ['torpedo'],
            'cannon': ['cannon'],
            'railgun': ['railgun'],
            'flak': ['flak']
        }
        
        for weapon_type, patterns in type_patterns.items():
            for pattern in patterns:
                if pattern in weapon_id_lower:
                    return weapon_type
        
        return 'unknown'
    
    def classify_turret_type(self, turret_id: str) -> str:
        """Classify turret type based on name patterns."""
        turret_id_lower = turret_id.lower()
        
        type_patterns = {
            'beam': ['beam', 'laser'],
            'plasma': ['plasma'],
            'particle': ['particle', 'ion'],
            'pulse': ['pulse', 'burst'],
            'mining': ['mining'],
            'missile': ['missile'],
            'torpedo': ['torpedo'],
            'cannon': ['cannon'],
            'railgun': ['railgun'],
            'flak': ['flak'],
            'point_defense': ['pointdefense', 'pd'],
            'destroyer': ['destroyer']
        }
        
        for turret_type, patterns in type_patterns.items():
            for pattern in patterns:
                if pattern in turret_id_lower:
                    return turret_type
        
        return 'unknown'
    
    def scan_weapon_systems(self):
        """Scan all WeaponSystems directories for weapons and turrets."""
        print("Scanning WeaponSystems directories...")
        
        weapon_count = 0
        turret_count = 0
        
        for weapon_systems_path in self.weapon_systems_paths:
            if not weapon_systems_path.exists():
                continue
                
            print(f"Processing: {weapon_systems_path}")
            
            # Recursively find all macro files
            for macro_file in weapon_systems_path.rglob("*_macro.xml"):
                try:
                    # Determine if it's a weapon or turret based on filename
                    if macro_file.name.startswith('weapon_'):
                        weapon_data = self.parse_weapon_macro(macro_file)
                        if weapon_data:
                            self.weapons_data.append(weapon_data)
                            weapon_count += 1
                    
                    elif macro_file.name.startswith('turret_'):
                        turret_data = self.parse_turret_macro(macro_file)
                        if turret_data:
                            self.turrets_data.append(turret_data)
                            turret_count += 1
                            
                except Exception as e:
                    print(f"Error processing {macro_file}: {e}")
                    continue
        
        print(f"Found {weapon_count} weapons and {turret_count} turrets")
    
    def generate_weapon_csv(self, output_path: Path):
        """Generate weapons CSV file."""
        if not self.weapons_data:
            print("No weapon data to export")
            return
        
        df = pd.DataFrame(self.weapons_data)
        
        # Sort by faction, size, type, mk level
        df = df.sort_values(['faction', 'size_class', 'weapon_type', 'mk_level'])
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        print(f"Exported {len(df)} weapons to {output_path}")
    
    def generate_turret_csv(self, output_path: Path):
        """Generate turrets CSV file."""
        if not self.turrets_data:
            print("No turret data to export")
            return
        
        df = pd.DataFrame(self.turrets_data)
        
        # Sort by faction, size, type, mk level
        df = df.sort_values(['faction', 'size_class', 'turret_type', 'mk_level'])
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        print(f"Exported {len(df)} turrets to {output_path}")


def generate_all_csvs():
    """Generate all CSV files (weapons, turrets, ships, engines, shields)."""
    print("=== Starting CSV Generation ===")
    
    # Load text mappings for localization
    load_text_mappings()
    
    # Create output directory for CSV files
    csv_output_dir = Path("data/csv_cache")
    csv_output_dir.mkdir(exist_ok=True)
    
    # Generate weapons and turrets CSV
    generator = WeaponCSVGenerator()
    generator.scan_weapon_systems()
    
    weapons_csv = csv_output_dir / "weapons.csv"
    turrets_csv = csv_output_dir / "turrets.csv"
    
    generator.generate_weapon_csv(weapons_csv)
    generator.generate_turret_csv(turrets_csv)
    
    # TODO: Also regenerate ships, engines, and shields CSV files here
    # For now, we'll focus on weapons and turrets
    
    print("=== CSV Generation Complete ===")
    print(f"CSV files saved to: {csv_output_dir}")
    

if __name__ == "__main__":
    generate_all_csvs()