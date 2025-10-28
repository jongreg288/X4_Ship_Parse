# Test final comprehensive engine filtering with spacesuits
import sys
sys.path.append('c:/Users/pheno/Code_Projects/X4_Ship_Parse')

from app.data_parser import load_engine_data, load_ship_data

# Load data
engines_df = load_engine_data()
ships_df = load_ship_data(engines_df)

print("=== FINAL COMPREHENSIVE ENGINE FILTERING TEST ===")

# Simulate the final GUI filtering logic
all_engines = engines_df
included_engines = []
excluded_engines = []
exclusion_categories = {
    'xs': [],
    'missile': [],
    'mine': [],
    'torpedo': [],
    'drone': [],
    'escapepod': [],
    'police': [],
    'spacesuit': []
}

for _, row in all_engines.iterrows():
    macro_name = row.get('name', 'Unknown')
    macro_lower = macro_name.lower()
    
    # Categorize excluded engines
    excluded = False
    if '_xs_' in macro_lower:
        exclusion_categories['xs'].append(macro_name)
        excluded = True
    elif 'missile' in macro_lower:
        exclusion_categories['missile'].append(macro_name)
        excluded = True
    elif 'mine' in macro_lower:
        exclusion_categories['mine'].append(macro_name)
        excluded = True
    elif 'torpedo' in macro_lower:
        exclusion_categories['torpedo'].append(macro_name)
        excluded = True
    elif 'drone' in macro_lower:
        exclusion_categories['drone'].append(macro_name)
        excluded = True
    elif 'escapepod' in macro_lower:
        exclusion_categories['escapepod'].append(macro_name)
        excluded = True
    elif 'police' in macro_lower:
        exclusion_categories['police'].append(macro_name)
        excluded = True
    elif 'spacesuit' in macro_lower:
        exclusion_categories['spacesuit'].append(macro_name)
        excluded = True
    
    if excluded:
        excluded_engines.append(macro_name)
    else:
        included_engines.append(macro_name)

print(f"Total engines: {len(all_engines)}")
print(f"Excluded engines: {len(excluded_engines)}")
print(f"Included ship engines: {len(included_engines)}")
print(f"Final exclusion rate: {len(excluded_engines)/len(all_engines)*100:.1f}%")

print(f"\n=== EXCLUSION BREAKDOWN ===")
for category, engines in exclusion_categories.items():
    if engines:
        print(f"{category.upper()}: {len(engines)} engines")
        for engine in engines:
            engine_row = all_engines[all_engines['name'] == engine].iloc[0]
            display_name = engine_row.get('display_name', engine)
            print(f"  {engine} → {display_name}")

print(f"\n=== SAMPLE FINAL INCLUDED ENGINES (First 10) ===")
for engine in included_engines[:10]:
    engine_row = all_engines[all_engines['name'] == engine].iloc[0]
    display_name = engine_row.get('display_name', engine)
    print(f"  {engine} → {display_name}")

print(f"\n=== SUCCESS! Final engine filtering complete - {len(included_engines)} ship engines remain! ===")