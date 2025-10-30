#!/usr/bin/env python3
"""
Simple shield parsing test that runs from the project root.
Run with: python -m src.tests.test_shield_simple
"""

def test_shield_parsing():
    """Test shield parsing by running the main app and checking output."""
    print("🔍 Testing shield parsing functionality...")
    
    # Import the modules we need - run from project root
    try:
        from src.data_parser import load_ship_data, load_engine_data
        print("✅ Successfully imported data parser functions")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    try:
        # Load engine data first (required for ship loading)
        print("🔄 Loading engine data...")
        engines_df = load_engine_data()
        print(f"✅ Loaded {len(engines_df)} engines")
        
        # Load ship data with shield parsing
        print("🔄 Loading ship data with shield parsing...")
        ships_df = load_ship_data(engines_df)
        ships_data = ships_df.to_dict('records')
        print(f"✅ Loaded {len(ships_data)} ships successfully")
        
        # Count ships with shield data
        ships_with_shields = [ship for ship in ships_data if ship.get('shield_connections', 0) > 0]
        print(f"📊 Ships with shield hardpoints: {len(ships_with_shields)}")
        
        # Check for the Argon bomber specifically
        bomber_ships = [ship for ship in ships_data 
                       if 'bomber' in ship.get('macro_name', '').lower() 
                       and 'arg' in ship.get('macro_name', '').lower()]
        
        if bomber_ships:
            bomber = bomber_ships[0]
            shield_connections = bomber.get('shield_connections', 0)
            shield_size_class = bomber.get('shield_size_class', 'Unknown')
            
            print(f"\n🎯 Argon Bomber Test:")
            print(f"  • Ship: {bomber.get('display_name', bomber.get('macro_name'))}")
            print(f"  • Shield Connections: {shield_connections}")
            print(f"  • Shield Size Class: {shield_size_class}")
            
            # Validate results
            success = True
            if shield_connections == 2:
                print(f"  ✅ Expected 2 shield hardpoints - PASS")
            else:
                print(f"  ❌ Expected 2 shield hardpoints, got {shield_connections} - FAIL")
                success = False
                
            if shield_size_class == 'm':
                print(f"  ✅ Expected 'M' size class - PASS")
            else:
                print(f"  ❌ Expected 'M' size class, got '{shield_size_class}' - FAIL")
                success = False
                
            return success
        else:
            print(f"❌ Could not find Argon bomber for testing")
            return False
            
    except Exception as e:
        print(f"💥 Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_shield_parsing()
    if success:
        print(f"\n🎉 Shield parsing test PASSED!")
    else:
        print(f"\n💥 Shield parsing test FAILED!")
        exit(1)