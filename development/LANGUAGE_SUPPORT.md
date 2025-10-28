# X4 Ship Parser - Language Support

## Multi-Language Ship Name Support

The X4 Ship Parser now includes **automatic language detection** and **multi-language support** for ship and engine names!

### ✨ Features

- **🌍 Automatic Language Detection**: Detects your preferred language from:
  1. X4 game configuration files
  2. Steam language settings  
  3. Windows system locale
  
- **🎯 Manual Language Override**: Choose any supported language through the GUI

- **📝 Real-time Language Switching**: Change languages on-the-fly via Settings menu

- **🔄 Smart Fallback**: Uses English if preferred language unavailable

### 🗣️ Supported Languages

The parser supports all X4 language packs:

| Language | Code | File |
|----------|------|------|
| 🇺🇸 English | 44 | `0001-l044.xml` |
| 🇩🇪 German | 49 | `0001-l049.xml` |
| 🇫🇷 French | 33 | `0001-l033.xml` |
| 🇪🇸 Spanish | 34 | `0001-l034.xml` |
| 🇪🇸 Spanish (Latin America) | 55 | `0001-l055.xml` |
| 🇮🇹 Italian | 39 | `0001-l039.xml` |
| 🇷🇺 Russian | 7 | `0001-l007.xml` |
| 🇵🇱 Polish | 48 | `0001-l048.xml` |
| 🇨🇿 Czech | 42 | `0001-l042.xml` |
| 🇹🇷 Turkish | 90 | `0001-l090.xml` |
| 🇯🇵 Japanese | 81 | `0001-l081.xml` |
| 🇰🇷 Korean | 82 | `0001-l082.xml` |
| 🇨🇳 Chinese (Simplified) | 86 | `0001-l086.xml` |
| 🇹🇼 Chinese (Traditional) | 88 | `0001-l088.xml` |

### 🎮 How It Works

1. **Extraction**: The parser automatically extracts the appropriate language file from your X4 installation's `lang.dat` archive

2. **Detection**: Uses intelligent priority system:
   - X4 game settings (highest priority)
   - Steam language preference
   - Windows system locale (fallback)

3. **Resolution**: Ship and engine names are resolved using 71,000+ text mappings from the selected language

### 🛠️ Usage

#### GUI Method (Recommended)
1. Launch X4 Ship Parser
2. Go to **Settings → Language...**
3. Choose automatic detection or select manually
4. Click OK to apply changes

#### Developer Method
```python
from app.language_detector import language_detector

# Set manual override
language_detector.set_user_override(49)  # German

# Clear override (back to auto-detection)  
language_detector.clear_user_override()

# Get current language info
lang_id = language_detector.get_language_id()
lang_name = language_detector.get_language_name()
```

### 📊 Examples

**English (ID: 44)**
- `{20101,11001}` → "Behemoth"
- `{20107,1401}` → "Travel Engine"
- `{1001,1}` → "Hull"

**German (ID: 49)**  
- `{20101,11001}` → "Behemoth"
- `{20107,1401}` → "Reiseantrieb"
- `{1001,1}` → "Hülle"

**Russian (ID: 7)**
- `{20101,11001}` → "Бегемот"  
- `{20107,1401}` → "Круизный двигатель"
- `{1001,1}` → "Корпус"

### 🔧 Technical Details

- **Language Files**: Automatically extracted from `lang.dat` using XRCatTool
- **Text Mappings**: ~71,096 text entries per language
- **Fallback System**: English used if preferred language unavailable
- **Memory Efficient**: Only loads one language at a time
- **Cache System**: Avoids reloading same language repeatedly

### 🚀 What's New

- ✅ Dynamic language detection from X4 game files
- ✅ Automatic extraction of correct language pack from `lang.dat`
- ✅ GUI language selection dialog with preview
- ✅ Support for all 14+ X4 languages
- ✅ Intelligent fallback to English
- ✅ Real-time language switching
- ✅ Integration with existing ship/engine name resolution

### 📝 Notes

- Language files are extracted directly from your X4 installation
- The executable automatically detects and uses your preferred language
- Ship names will appear in your selected language throughout the interface
- Language preference is remembered between sessions
- All 71,000+ text mappings are available in each supported language

---

*This feature makes the X4 Ship Parser truly international! 🌍*