"""
Test script to demonstrate X4 language detection and selection capabilities.
This script shows how to:
1. Detect current system language
2. List available languages  
3. Set manual language overrides
4. Test language file loading
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.language_detector import language_detector, X4_LANGUAGE_MAP
from app.data_parser import load_text_mappings, get_current_language_info, refresh_text_mappings


def main():
    print("🌍 X4 Language Detection & Selection Test")
    print("=" * 50)
    
    # Show current detection
    print("1. Current Language Detection:")
    current_id = language_detector.get_language_id()
    current_name = language_detector.get_language_name()
    current_file = language_detector.get_language_file_name()
    print(f"   → Detected: {current_name} (ID: {current_id})")
    print(f"   → File: {current_file}")
    
    # Show available languages
    print("\n2. Available Languages:")
    for lang_id, lang_name in sorted(X4_LANGUAGE_MAP.items(), key=lambda x: x[1]):
        marker = " ← Current" if lang_id == current_id else ""
        print(f"   {lang_id:2d}: {lang_name}{marker}")
    
    # Test text mappings loading
    print("\n3. Testing Text Mappings:")
    try:
        load_text_mappings()
        info = get_current_language_info()
        print(f"   ✅ Loaded {info['mapping_count']} text entries")
        print(f"   📄 From file: {info['language_file']}")
        
        # Test a few text references
        from app.data_parser import resolve_text_reference_advanced
        
        test_refs = [
            "{20101,11001}",  # Common ship name reference
            "{20107,1401}",   # Common engine reference
            "{1001,1}",       # "Hull"
            "{1001,5}",       # "Ship"
        ]
        
        print("\n   Sample Text Resolutions:")
        for ref in test_refs:
            resolved = resolve_text_reference_advanced(ref)
            if resolved != ref:  # Only show if resolved
                print(f"     {ref} → '{resolved}'")
                
    except Exception as e:
        print(f"   ❌ Error loading text mappings: {e}")
    
    # Demonstrate language override
    print("\n4. Language Override Demonstration:")
    
    # Try German if available
    if 7 in X4_LANGUAGE_MAP:  # German
        print("   Testing German override...")
        try:
            language_detector.set_user_override(7)
            print(f"   → Override set to: {language_detector.get_language_name()}")
            print(f"   → File would be: {language_detector.get_language_file_name()}")
            
            # Clear override
            language_detector.clear_user_override()
            print("   → Override cleared - back to auto-detection")
            
        except Exception as e:
            print(f"   ⚠️ Override test failed: {e}")
    
    print("\n5. Language File Validation:")
    data_dir = Path("data")
    if data_dir.exists():
        # Check which language files actually exist
        t_dir = data_dir / "t"
        if t_dir.exists():
            found_files = []
            for lang_id, lang_name in X4_LANGUAGE_MAP.items():
                lang_file = f"0001-l{lang_id:03d}.xml"
                if (t_dir / lang_file).exists():
                    found_files.append((lang_id, lang_name, lang_file))
            
            if found_files:
                print("   Available language files:")
                for lang_id, lang_name, lang_file in found_files:
                    print(f"     ✓ {lang_name}: {lang_file}")
            else:
                print("   ⚠️ No language files found in data/t/")
        else:
            print("   ⚠️ No data/t/ directory found")
    else:
        print("   ⚠️ No data directory found")
    
    print("\n✅ Language detection test completed!")
    print("\nTo use different languages:")
    print("1. Make sure the language file exists in data/t/")
    print("2. Use Settings → Language... in the GUI")
    print("3. Or set language_detector.set_user_override(language_id) in code")


if __name__ == "__main__":
    main()