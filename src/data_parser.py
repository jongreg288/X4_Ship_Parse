import xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
from .language_detector import language_detector

UNITS_DIR = Path("data/assets/units")

# Text mappings loaded from X4 localization files
TEXT_MAPPINGS = {}
CURRENT_LANGUAGE_FILE = None

def load_text_mappings():
    """Load text mappings from X4 localization files with dynamic language detection."""
    global TEXT_MAPPINGS, CURRENT_LANGUAGE_FILE
    
    # Detect current language
    detected_lang_id = language_detector.get_language_id()
    lang_file = language_detector.get_language_file_name(detected_lang_id)
    lang_name = language_detector.get_language_name(detected_lang_id)
    
    # Check if we've already loaded this language file
    if TEXT_MAPPINGS and CURRENT_LANGUAGE_FILE == lang_file:
        return
    
    # Clear existing mappings when switching languages
    TEXT_MAPPINGS.clear()
    
    text_file = Path("data/t") / lang_file
    
    # Try fallback to English if preferred language file doesn't exist
    if not text_file.exists():
        fallback_file = Path("data/t/0001-l044.xml")
        if fallback_file.exists():
            print(f"⚠️ {lang_name} text file not found: {text_file}")
            print(f"🔄 Using English fallback: {fallback_file}")
            text_file = fallback_file
            lang_name = "English (fallback)"
        else:
            print(f"❌ No text files found - neither {text_file} nor English fallback")
            return
    
    try:
        tree = ET.parse(text_file)
        root = tree.getroot()
        
        # Verify this is a valid language file
        if root.tag != "language":
            print(f"⚠️ Invalid language file format: {text_file}")
            return
            
        file_lang_id = root.get("id")
        print(f"🌍 Loading {lang_name} text mappings from {text_file.name} (Language ID: {file_lang_id})")
        
        # Parse all pages and text entries
        for page in root.findall(".//page"):
            page_id = page.get("id")
            if page_id:
                for text_entry in page.findall("t"):
                    text_id = text_entry.get("id")
                    text_value = text_entry.text or ""
                    if text_id:
                        key = f"{{{page_id},{text_id}}}"
                        # Clean up escaped characters
                        clean_value = text_value.strip().replace("\\(", "(").replace("\\)", ")")
                        TEXT_MAPPINGS[key] = clean_value
        
        CURRENT_LANGUAGE_FILE = lang_file
        print(f"✅ Loaded {len(TEXT_MAPPINGS)} text mappings from {lang_name} localization file")
        
    except ET.ParseError as e:
        print(f"❌ Failed to parse text file {text_file}: {e}")

def resolve_text_reference_advanced(text_ref):
    """Resolve a text reference using loaded mappings."""
    if not TEXT_MAPPINGS:
        load_text_mappings()
    
    return TEXT_MAPPINGS.get(text_ref, text_ref)


def refresh_text_mappings():
    """Force reload of text mappings (useful when language changes)."""
    global TEXT_MAPPINGS, CURRENT_LANGUAGE_FILE
    TEXT_MAPPINGS.clear()
    CURRENT_LANGUAGE_FILE = None
    load_text_mappings()


def get_current_language_info():
    """Get information about the currently loaded language."""
    lang_id = language_detector.get_language_id()
    lang_name = language_detector.get_language_name()
    lang_file = CURRENT_LANGUAGE_FILE or "Not loaded"
    mapping_count = len(TEXT_MAPPINGS)
    
    return {
        "language_id": lang_id,
        "language_name": lang_name,
        "language_file": lang_file,
        "mapping_count": mapping_count
    }

def construct_ship_name(basename_ref, variation_refs):
    """Construct full ship name from basename + variations."""
    if not basename_ref:
        return None
    
    # Resolve basename
    basename = resolve_text_reference_advanced(basename_ref)
    if basename.startswith("{"):
        basename = f"Ship {basename}"  # Fallback if not found
    
    # Resolve variations
    variations = []
    if variation_refs:
        # Split multiple references like "{20111,3101} {20111,1101}"
        refs = variation_refs.split()
        for ref in refs:
            ref = ref.strip()
            if ref.startswith("{") and ref.endswith("}"):
                variation = resolve_text_reference_advanced(ref)
                if not variation.startswith("{"):  # Successfully resolved
                    variations.append(variation)
    
    # Combine name parts
    if variations:
        return f"{basename} {' '.join(variations)}"
    else:
        return basename

def parse_complex_name_reference(name_ref):
    """Parse complex name references like '(Behemoth E){20101,11001} {20111,5462}'."""
    if not name_ref or not name_ref.startswith("("):
        return None
    
    import re
    
    # Pattern to match: (Display Name)reference1 reference2 ...
    pattern = r'\(([^)]+)\)(.+)'
    match = re.match(pattern, name_ref)
    
    if not match:
        return None
        
    display_part = match.group(1)  # e.g., "Behemoth E"
    refs_part = match.group(2).strip()  # e.g., "{20101,11001} {20111,5462}"
    
    # Extract and resolve text references
    ref_pattern = r'\{[^}]+\}'
    refs = re.findall(ref_pattern, refs_part)
    
    resolved_parts = []
    for ref in refs:
        resolved = resolve_text_reference_advanced(ref)
        if resolved and not resolved.startswith("{"):
            resolved_parts.append(resolved)
    
    # Try to construct the name intelligently
    if resolved_parts:
        # Construct name from resolved references
        base_name = resolved_parts[0] if resolved_parts else ""
        variations = resolved_parts[1:] if len(resolved_parts) > 1 else []
        
        # Clean up variations and combine properly
        clean_variations = []
        for var in variations:
            if var and not var.startswith("{"):
                clean_variations.append(var)
        
        if clean_variations:
            return f"{base_name} {' '.join(clean_variations)}"
        else:
            return base_name
    else:
        # Fallback to display part if no references resolved
        return display_part

def resolve_text_reference(text_ref):
    """Resolve a text reference like {20101,11102} to human-readable name (legacy function)."""
    return resolve_text_reference_advanced(text_ref)

def extract_storage_info(xml_file: Path, macro_el):
    """Extract storage information from connections section."""
    storage_cargo_max = 0
    storage_cargo_type = None
    
    # First, try to find storage reference in connections
    connections_el = macro_el.find("connections")
    if connections_el is not None:
        for connection in connections_el.findall("connection"):
            macro_ref = connection.find("macro")
            if macro_ref is not None:
                ref_name = macro_ref.get("ref", "")
                if "storage" in ref_name.lower():
                    # Find the storage macro file
                    storage_file = find_storage_macro(xml_file, ref_name)
                    if storage_file:
                        storage_max, storage_type = parse_storage_macro(storage_file)
                        if storage_max > 0:  # Found valid storage
                            storage_cargo_max = storage_max
                            storage_cargo_type = storage_type
                            break
    
    # Fallback: try the old naming convention approach
    if storage_cargo_max == 0:
        ship_name = xml_file.stem  # e.g., "ship_arg_l_miner_solid_01_a_macro"
        
        # Convert ship name to storage name by replacing "ship_" with "storage_"
        if ship_name.startswith("ship_"):
            storage_name = ship_name.replace("ship_", "storage_")
            
            # Find the storage macro file
            storage_file = find_storage_macro(xml_file, storage_name)
            if storage_file:
                storage_max, storage_type = parse_storage_macro(storage_file)
                storage_cargo_max = storage_max
                storage_cargo_type = storage_type
    
    return storage_cargo_max, storage_cargo_type

def find_storage_macro(ship_xml_file: Path, storage_ref: str) -> Path | None:
    """Find the storage macro XML file based on the reference."""
    # Try multiple possible locations for storage files
    possible_locations = [
        # Storage files alongside ship files (same directory)
        ship_xml_file.parent / f"{storage_ref}.xml",
        # Storage files in StorageModules
        Path("data/assets/props/StorageModules/macros") / f"{storage_ref}.xml",
        # In case there are other storage locations
        Path("data/assets/props/StorageModules") / f"{storage_ref}.xml"
    ]
    
    for storage_file in possible_locations:
        if storage_file.exists():
            return storage_file
    
    return None

def parse_storage_macro(storage_file: Path):
    """Parse storage macro file to extract cargo max and type."""
    try:
        tree = ET.parse(storage_file)
        root = tree.getroot()
        
        # Find cargo element in properties
        cargo_el = root.find(".//cargo")
        if cargo_el is not None:
            cargo_max = int(cargo_el.get("max", 0))
            cargo_tags = cargo_el.get("tags", "")
            return cargo_max, cargo_tags
    except ET.ParseError:
        print(f"⚠️ Failed to parse storage file {storage_file}")
    
    return 0, None

def load_ship_data(engines_df: pd.DataFrame) -> pd.DataFrame:
    ships = []

    # Iterate over all "size_*" folders, excluding XS ships
    for size_dir in UNITS_DIR.glob("size_*"):
        # Skip extra small ships - they're mostly drones, pods and utility vessels
        if size_dir.name == "size_xs":
            continue
            
        macros_dir = size_dir / "macros"
        if not macros_dir.exists():
            continue

        # Iterate over all ship macro XMLs
        for xml_file in macros_dir.glob("ship_*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
            except ET.ParseError:
                print(f"⚠️ Failed to parse {xml_file}")
                continue

            # Find the first <macro> element
            macro_el = root.find(".//macro")
            if macro_el is None:
                continue

            macro_name = macro_el.get("name")
            alias = macro_el.get("alias")
            ship_class = macro_el.get("class", "unknown")

            # Resolve alias if present
            if alias and alias.endswith("_macro"):
                macro_name = alias

            props = macro_el.find("properties")
            if props is None:
                print(f"⚠️ No <properties> found in {xml_file.name}")
                continue

            # Identification block
            ident = props.find("identification")
            maker_race = ident.get("makerrace") if ident is not None else None
            icon = ident.get("icon") if ident is not None else None
            desc = ident.get("description") if ident is not None else None
            name_ref = ident.get("name") if ident is not None else None
            basename_ref = ident.get("basename") if ident is not None else None
            variation_ref = ident.get("variation") if ident is not None else None

            # Hull
            hull_el = props.find("hull")
            hull_max = float(hull_el.get("max", 0)) if hull_el is not None else 0

            # Cargo
            cargo_el = props.find("cargo")
            cargo_max = int(cargo_el.get("max", 0)) if cargo_el is not None else 0
            cargo_tags = cargo_el.get("tags") if cargo_el is not None else None

            # Storage (like missile or drone storage)
            storage_el = props.find("storage")
            storage = None
            if storage_el is not None:
                # Combine all attributes into a single string, e.g. "missile=20, drone=5"
                storage = ", ".join(f"{k}={v}" for k, v in storage_el.attrib.items())

            # Physics data (mass, drag values)
            physics_el = props.find("physics")
            mass = 0.0
            drag_forward = 0.0
            drag_reverse = 0.0
            drag_horizontal = 0.0
            drag_vertical = 0.0
            if physics_el is not None:
                mass = float(physics_el.get("mass", 0))
                drag_el = physics_el.find("drag")
                if drag_el is not None:
                    drag_forward = float(drag_el.get("forward", 0))
                    drag_reverse = float(drag_el.get("reverse", 0))
                    drag_horizontal = float(drag_el.get("horizontal", 0))
                    drag_vertical = float(drag_el.get("vertical", 0))

            # Purpose information
            purpose_el = props.find("purpose")
            purpose_primary = purpose_el.get("primary") if purpose_el is not None else None

            # Component reference (not necessarily engine)
            component_el = macro_el.find("component")
            component_ref = component_el.get("ref") if component_el is not None else None

            # Count engine connections by looking for the associated component XML file
            engine_connections = 0
            if component_ref:
                # Look for the component file in the parent directory (not macros subfolder)
                component_file = xml_file.parent.parent / f"{component_ref}.xml"
                if component_file.exists():
                    try:
                        comp_tree = ET.parse(component_file)
                        comp_root = comp_tree.getroot()
                        # Count connections with "engine" in tags
                        engine_conns = [
                            conn for conn in comp_root.findall(".//connection")
                            if conn.get("tags") and "engine" in conn.get("tags", "")
                        ]
                        engine_connections = len(engine_conns)
                    except ET.ParseError:
                        print(f"⚠️ Failed to parse component file {component_file}")
                        engine_connections = 1  # Default fallback
                else:
                    engine_connections = 1  # Default fallback when no component file found

            # Check ship type and skip drones and non-ships
            ship_el = props.find("ship")
            ship_type = ship_el.get("type") if ship_el is not None else None
            if ship_type == "smalldrone":
                continue  # Skip small drones (mining/fighting drones)
            if ship_type == "lasertower":
                continue  # Skip laser towers (defensive structures)
            
            # Skip all transport drones (any ships with "transdrone" in filename)
            if "transdrone" in xml_file.name:
                continue  # Skip transport drones (small and medium)

            # Extract storage information from referenced storage components
            storage_cargo_max, storage_cargo_type = extract_storage_info(xml_file, macro_el)

            # Resolve human-readable name using multiple approaches
            if basename_ref and variation_ref:
                display_name = construct_ship_name(basename_ref, variation_ref)
            elif name_ref:
                # First resolve the reference, then check if result needs complex parsing
                resolved_name = resolve_text_reference_advanced(name_ref)
                # Check if the resolved text is a complex reference like "(Behemoth E){20101,11001} {20111,5462}"
                if resolved_name and resolved_name.startswith("(") and "{" in resolved_name:
                    complex_name = parse_complex_name_reference(resolved_name)
                    display_name = complex_name if complex_name else resolved_name
                else:
                    display_name = resolved_name
            else:
                display_name = macro_name

            ships.append({
                "macro_name": macro_name,
                "alias": alias,
                "class": ship_class,
                "maker_race": maker_race,
                "icon": icon,
                "description": desc,
                "name_ref": name_ref,
                "basename_ref": basename_ref,
                "variation_ref": variation_ref,
                "display_name": display_name,
                "hull_max": hull_max,
                "storage": storage,
                "storage_cargo_max": storage_cargo_max,
                "storage_cargo_type": storage_cargo_type,
                "purpose_primary": purpose_primary,
                "mass": mass,
                "drag (forward)": drag_forward,
                "drag (reverse)": drag_reverse,
                "drag (horizontal)": drag_horizontal,
                "drag (vertical)": drag_vertical,
                "engine_connections": engine_connections,
                "component_ref": component_ref,
                "file": str(xml_file)
            })

    ships_df = pd.DataFrame(ships)

    print(f"Loaded {len(ships_df)} ships from {UNITS_DIR}")

    # Optionally merge with engines if we have a matching ref (rare)
    if not ships_df.empty and not engines_df.empty:
        if "component_ref" in ships_df.columns and "name" in engines_df.columns:
            ships_df = ships_df.merge(
                engines_df,
                left_on="component_ref",
                right_on="name",
                how="left",
                suffixes=("", "_engine")
            )

    return ships_df

def load_engine_data(engine_dir="./data/assets/props/Engines/macros"):
    """
    Loads all engine macros from the specified folder.
    Returns a DataFrame with columns:
    name, travel_thrust, boost_thrust, forward_thrust, reverse_thrust
    """
    engine_dir = Path(engine_dir)
    if not engine_dir.exists():
        print(f"⚠️ Engine folder not found: {engine_dir}")
        return pd.DataFrame()

    engines = []

    for xml_file in engine_dir.glob("*.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError:
            print(f"⚠️ Failed to parse {xml_file}")
            continue

        for macro in root.findall(".//macro[@class='engine']"):
            macro_name = macro.attrib.get("name", "unknown_engine")
            props = macro.find("properties")
            travel_thrust = boost_thrust = forward_thrust = reverse_thrust = 0
            
            # Engine text references
            name_ref = basename_ref = shortname_ref = description_ref = maker_race = mk = None

            if props is not None:
                # Get identification info
                ident = props.find("identification")
                if ident is not None:
                    name_ref = ident.get("name")
                    basename_ref = ident.get("basename") 
                    shortname_ref = ident.get("shortname")
                    description_ref = ident.get("description")
                    maker_race = ident.get("makerrace")
                    mk = ident.get("mk")
                
                # Travel thrust
                travel = props.find("travel")
                if travel is not None:
                    travel_thrust = float(travel.attrib.get("thrust", 0))
                # Boost thrust
                boost = props.find("boost")
                if boost is not None:
                    boost_thrust = float(boost.attrib.get("thrust", 0))
                # Forward/reverse thrust
                thrust = props.find("thrust")
                if thrust is not None:
                    forward_thrust = float(thrust.attrib.get("forward", 0))
                    reverse_thrust = float(thrust.attrib.get("reverse", 0))

            # Resolve human-readable name using basename or name reference
            display_name = macro_name  # fallback
            if basename_ref:
                resolved_basename = resolve_text_reference_advanced(basename_ref)
                if resolved_basename:
                    # Check if the resolved text is a complex reference like "(Travel Engine){20107,1401}"
                    if resolved_basename.startswith("(") and "{" in resolved_basename:
                        complex_name = parse_complex_name_reference(resolved_basename)
                        base_name = complex_name if complex_name else resolved_basename
                    else:
                        base_name = resolved_basename
                    
                    # Add mark/version info if available
                    if mk:
                        display_name = f"{base_name} Mk{mk}"
                    else:
                        display_name = base_name
            elif name_ref:
                resolved_name = resolve_text_reference_advanced(name_ref)
                if resolved_name:
                    # Check if the resolved text is a complex reference
                    if resolved_name.startswith("(") and "{" in resolved_name:
                        complex_name = parse_complex_name_reference(resolved_name)
                        display_name = complex_name if complex_name else resolved_name
                    else:
                        display_name = resolved_name

            engines.append({
                "name": macro_name,
                "display_name": display_name,
                "basename_ref": basename_ref,
                "name_ref": name_ref,
                "shortname_ref": shortname_ref,
                "description_ref": description_ref,
                "maker_race": maker_race,
                "mk": mk,
                "travel_thrust": travel_thrust,
                "boost_thrust": boost_thrust,
                "forward_thrust": forward_thrust,
                "reverse_thrust": reverse_thrust
            })

    df = pd.DataFrame(engines)
    print(f"Loaded {len(df)} engines from {engine_dir}")
    return df
