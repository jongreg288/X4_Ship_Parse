"""
X4 Language Detection Module

This module handles:
1. Detecting system language
2. Reading X4 game language preferences
3. Mapping to X4 language IDs
4. Providing language file paths
"""

import os
import sys
import locale
import winreg
from pathlib import Path
from typing import Optional, Dict, Tuple
import xml.etree.ElementTree as ET


# X4 Language ID mappings (from actual X4 game files)
X4_LANGUAGE_MAP = {
    7: "Russian",               # ID 7: "Корпус"
    33: "French",               # ID 33: "Coque"  
    34: "Spanish",              # ID 34: "Casco"
    39: "Italian",              # ID 39: "Scafo"
    42: "Czech",                # ID 42: "Trup"
    44: "English",              # ID 44: "Hull"
    48: "Polish",               # ID 48: "Kadłub"
    49: "German",               # ID 49: "Hülle"
    55: "Spanish (Latin America)", # ID 55: "Casco"
    81: "Japanese",             # ID 81: "船体"
    82: "Korean",               # ID 82: "선체"
    86: "Chinese (Simplified)", # ID 86: "船体"
    88: "Chinese (Traditional)", # ID 88: "船體"
    90: "Turkish",              # ID 90: "Gövde"
    359: "Russian (Alternative)", # ID 359: "Корпус" 
    380: "Russian (Alternative 2)" # ID 380: "Корпус"
}

# Map Windows locale codes to X4 language IDs (corrected based on actual X4 files)
LOCALE_TO_X4_MAP = {
    # English variants
    "en": 44, "en_US": 44, "en_GB": 44, "en_CA": 44, "en_AU": 44,
    # German variants 
    "de": 49, "de_DE": 49, "de_AT": 49, "de_CH": 49,  # German is ID 49, not 7
    # French variants
    "fr": 33, "fr_FR": 33, "fr_CA": 33, "fr_BE": 33, "fr_CH": 33,
    # Spanish variants
    "es": 34, "es_ES": 34, "es_MX": 55, "es_AR": 55, "es_CL": 55,  # Latin America uses ID 55
    # Italian
    "it": 39, "it_IT": 39,
    # Russian variants
    "ru": 7, "ru_RU": 7,  # Russian is ID 7, not 49
    # Polish
    "pl": 48, "pl_PL": 48,  # Polish is ID 48, not 55
    # Czech
    "cs": 42, "cs_CZ": 42,
    # Turkish
    "tr": 90, "tr_TR": 90,
    # Japanese
    "ja": 81, "ja_JP": 81,
    # Korean
    "ko": 82, "ko_KR": 82,
    # Chinese variants
    "zh_CN": 86, "zh_Hans": 86,  # Simplified Chinese
    "zh_TW": 88, "zh_Hant": 88,  # Traditional Chinese
}


class X4LanguageDetector:
    """Handles detection of appropriate X4 language based on system and game settings."""
    
    def __init__(self):
        self._cached_language_id: Optional[int] = None
        self._user_override: Optional[int] = None
        
    def detect_system_language(self) -> int:
        """Detect system language and map to X4 language ID."""
        try:
            # Get system locale 
            system_locale = locale.getdefaultlocale()[0]
            
            if system_locale:
                # Try exact match first
                if system_locale in LOCALE_TO_X4_MAP:
                    return LOCALE_TO_X4_MAP[system_locale]
                
                # Try base language (e.g., 'en' from 'en_US')
                base_lang = system_locale.split('_')[0]
                if base_lang in LOCALE_TO_X4_MAP:
                    return LOCALE_TO_X4_MAP[base_lang]
                    
        except Exception as e:
            print(f"⚠️ Could not detect system language: {e}")
            
        # Default to English if detection fails
        return 44
        
    def detect_x4_game_language(self, x4_install_path: Path) -> Optional[int]:
        """Detect X4 game language from game configuration files."""
        try:
            # Check for X4 config file locations
            config_paths = [
                x4_install_path / "config.xml",
                Path.home() / "Documents" / "Egosoft" / "X4" / "config.xml",
                Path.home() / "Documents" / "Egosoft" / "X4 Foundations" / "config.xml"
            ]
            
            for config_path in config_paths:
                if config_path.exists():
                    try:
                        tree = ET.parse(config_path)
                        root = tree.getroot()
                        
                        # Look for language setting in config
                        lang_elem = root.find(".//language")
                        if lang_elem is not None and lang_elem.text:
                            try:
                                lang_id = int(lang_elem.text)
                                if lang_id in X4_LANGUAGE_MAP:
                                    print(f"✅ Found X4 game language setting: {X4_LANGUAGE_MAP[lang_id]} (ID: {lang_id})")
                                    return lang_id
                            except ValueError:
                                continue
                                
                    except ET.ParseError:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Could not read X4 game language setting: {e}")
            
        return None
        
    def detect_steam_language(self) -> Optional[int]:
        """Detect Steam language preference from Windows registry."""
        try:
            # Try to read Steam language from registry
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                language, _ = winreg.QueryValueEx(key, "Language")
                
                # Map common Steam language codes to X4 IDs (corrected)
                steam_to_x4 = {
                    "english": 44,
                    "german": 49,    # German is ID 49
                    "french": 33,
                    "spanish": 34,
                    "italian": 39,
                    "russian": 7,    # Russian is ID 7
                    "polish": 48,    # Polish is ID 48
                    "czech": 42,
                    "turkish": 90,
                    "japanese": 81,
                    "korean": 82,
                    "schinese": 86,  # Simplified Chinese
                    "tchinese": 88   # Traditional Chinese
                }
                
                if language.lower() in steam_to_x4:
                    steam_lang_id = steam_to_x4[language.lower()]
                    print(f"✅ Found Steam language: {X4_LANGUAGE_MAP[steam_lang_id]} (ID: {steam_lang_id})")
                    return steam_lang_id
                    
        except (FileNotFoundError, OSError, KeyError):
            pass
            
        return None
        
    def get_language_id(self, x4_install_path: Optional[Path] = None) -> int:
        """Get the best language ID using priority: user override > X4 config > Steam > system."""
        
        # Return cached result if available
        if self._cached_language_id is not None:
            return self._cached_language_id
            
        # Check user override first
        if self._user_override is not None:
            print(f"🎯 Using user-selected language: {X4_LANGUAGE_MAP[self._user_override]} (ID: {self._user_override})")
            self._cached_language_id = self._user_override
            return self._user_override
            
        print("🔍 Detecting language preference...")
        
        # Try X4 game config first (highest priority)
        if x4_install_path:
            x4_lang = self.detect_x4_game_language(x4_install_path)
            if x4_lang:
                self._cached_language_id = x4_lang
                return x4_lang
                
        # Try Steam language setting
        steam_lang = self.detect_steam_language()
        if steam_lang:
            self._cached_language_id = steam_lang
            return steam_lang
            
        # Fall back to system language
        system_lang = self.detect_system_language()
        print(f"🌍 Using system language: {X4_LANGUAGE_MAP[system_lang]} (ID: {system_lang})")
        self._cached_language_id = system_lang
        return system_lang
        
    def set_user_override(self, language_id: int):
        """Set user-selected language override."""
        if language_id in X4_LANGUAGE_MAP:
            self._user_override = language_id
            self._cached_language_id = None  # Clear cache
            print(f"🎯 Language override set to: {X4_LANGUAGE_MAP[language_id]} (ID: {language_id})")
        else:
            raise ValueError(f"Invalid language ID: {language_id}")
            
    def clear_user_override(self):
        """Clear user language override."""
        self._user_override = None
        self._cached_language_id = None  # Clear cache
        print("🔄 Language override cleared - will auto-detect")
        
    def get_language_file_name(self, language_id: Optional[int] = None) -> str:
        """Get the language file name for the specified or detected language ID."""
        if language_id is None:
            language_id = self.get_language_id()
        return f"0001-l{language_id:03d}.xml"
        
    def get_language_name(self, language_id: Optional[int] = None) -> str:
        """Get the human-readable language name."""
        if language_id is None:
            language_id = self.get_language_id()
        return X4_LANGUAGE_MAP.get(language_id, f"Unknown (ID: {language_id})")
        
    def get_available_languages(self) -> Dict[int, str]:
        """Get all available X4 languages."""
        return X4_LANGUAGE_MAP.copy()
        
    def validate_language_file(self, data_dir: Path, language_id: Optional[int] = None) -> Tuple[bool, str]:
        """Validate that the language file exists and is readable."""
        if language_id is None:
            language_id = self.get_language_id()
            
        lang_file = data_dir / "t" / self.get_language_file_name(language_id)
        
        if not lang_file.exists():
            return False, f"Language file not found: {lang_file}"
            
        try:
            tree = ET.parse(lang_file)
            root = tree.getroot()
            
            # Verify it's a valid language file
            if root.tag != "language":
                return False, f"Invalid language file format: {lang_file}"
                
            file_lang_id = root.get("id")
            if file_lang_id != str(language_id):
                return False, f"Language ID mismatch: expected {language_id}, found {file_lang_id}"
                
            # Count text entries
            text_count = len(root.findall(".//t"))
            if text_count == 0:
                return False, f"No text entries found in language file: {lang_file}"
                
            return True, f"Valid language file with {text_count} text entries"
            
        except ET.ParseError as e:
            return False, f"Failed to parse language file: {e}"


# Global instance for easy access
language_detector = X4LanguageDetector()


def get_current_language_id(x4_install_path: Optional[Path] = None) -> int:
    """Convenience function to get current language ID."""
    return language_detector.get_language_id(x4_install_path)


def get_current_language_file() -> str:
    """Convenience function to get current language file name."""
    return language_detector.get_language_file_name()


def get_current_language_name() -> str:
    """Convenience function to get current language name."""
    return language_detector.get_language_name()


if __name__ == "__main__":
    # Test the language detection
    detector = X4LanguageDetector()
    
    print("🌍 X4 Language Detection Test")
    print("=" * 40)
    
    system_lang = detector.detect_system_language()
    print(f"System Language: {X4_LANGUAGE_MAP[system_lang]} (ID: {system_lang})")
    
    steam_lang = detector.detect_steam_language()
    if steam_lang:
        print(f"Steam Language: {X4_LANGUAGE_MAP[steam_lang]} (ID: {steam_lang})")
    else:
        print("Steam Language: Not detected")
        
    final_lang = detector.get_language_id()
    print(f"Selected Language: {X4_LANGUAGE_MAP[final_lang]} (ID: {final_lang})")
    print(f"Language File: {detector.get_language_file_name()}")
    
    print("\nAvailable Languages:")
    for lang_id, lang_name in detector.get_available_languages().items():
        print(f"  {lang_id:2d}: {lang_name}")