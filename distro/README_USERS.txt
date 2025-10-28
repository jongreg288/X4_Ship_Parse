# X4 Ship Parser v0.1.3 Alpha - Multi-Language Edition (Hopefully) 🌍

## About
X4 Ship Parser is a comprehensive tool for analyzing X4: Foundations ship statistics with **automatic language detection** and **intelligent data extraction**. Supports 14+ languages and provides clean, windowed interface with **interactive visual comparisons**.

## ✨ Key Features
- **🌍 Multi-Language Support**: Automatic detection of your preferred language
- **📊 Advanced Ship Analysis**: Compare 166+ ships with detailed statistics
- **📈 Visual Comparisons**: Interactive charts showing cargo/speed rankings for top 5 ships
- **🔄 Smart Engine Filtering**: Cascading dropdowns auto-filter engines by ship size (S/M/L/XL)
- **⚡ Smart Data Extraction**: Direct CAT/DAT reading with minimal extraction
- **🎨 Clean Interface**: Windowed GUI without console windows  
- **🎯 Purpose-Based Filtering**: Fighters, Container Ships, Solid/Liquid Cargo
- **🔄 Flexible Updates**: Choose automatic or manual update checking
- **📝 Intelligent Names**: Ship/engine names in clean, readable format

## 🌍 Supported Languages
English, German, French, Spanish, Italian, Russian, Polish, Czech, Turkish, Japanese, Korean, Chinese (Simplified & Traditional), and more.

## System Requirements
- **OS**: Windows 10/11 64-bit
- **RAM**: 200MB minimum  
- **Storage**: 500MB free space (optimized extraction)
- **Game**: X4: Foundations (Steam, Epic Games, or GOG)
- **Network**: Optional (for automatic updates only)

## 📦 Installation Options

### Full Package (Recommended) - 93 MB
1. Download `X4_Ship_Parser.exe` + `X4_Updater.exe`
2. Place both files in the same folder
3. Run `X4_Ship_Parser.exe`
4. Enjoy automatic update checking

### Standalone Package - 78.5 MB  
1. Download `X4_Ship_Parser.exe` only
2. Place in any folder
3. Run `X4_Ship_Parser.exe`
4. Use Help → Check for Updates for manual updates

## 🚀 Quick Start
1. **Launch**: Double-click `X4_Ship_Parser.exe`
2. **Auto-Setup**: Application detects X4 and extracts needed data
3. **Language**: Automatically uses your system/game language
4. **Analyze**: Compare ships and engines across 4 categories

## 🎮 Interface Guide
1. **Select Category**: Choose Fighters, Container, Solid, or Liquid
2. **Pick Ship**: Select from dropdown of relevant ships
3. **Choose Engine**: Engine list automatically filters to matching ship size
4. **View Results**: See travel speeds, cargo capacity, and detailed statistics
5. **Compare Visually**: Bar chart shows top 5 ships of same size with selected engine
6. **Language**: Settings → Language to change interface language

## 🆕 What's New in v0.1.3

### Visual Enhancements
- **📊 Interactive Comparison Charts**: Matplotlib-based bar charts display top 5 ships
  - Automatically compares ships of the same size class
  - Shows cargo/speed ratio rankings
  - Highlights your selected ship in green
  - Updates in real-time as you change selections

### Smart Filtering
- **🔄 Cascading Engine Dropdown**: Engine list now intelligently filters based on ship size
  - Select an S-size ship → See only S-size engines
  - Select an M-size ship → See only M-size engines  
  - Select an L-size ship → See only L-size engines
  - Select an XL-size ship → See only XL-size engines
  - No more scrolling through incompatible engines!

### Improved Display
- **📝 Cleaner Engine Names**: New format shows "FACTION SIZE Type Variant"
  - Example: "ARG L Allround MK3" instead of "engine_arg_l_allround_01_mk3_macro"
  - Easier to read and compare at a glance
  - Includes size class for quick identification

### User Experience
- **⚠️ DLC Notice**: Added disclaimer about DLC ships (not yet supported)
- **🎯 Better Tooltips**: More detailed information on hover
- **🔧 Bug Fixes**: Fixed engine dropdown showing only 2 items after filtering

## Tab Organization
- **Fighters**: Combat ships (87 ships) - purpose: fight
- **Container**: Trade ships (82 ships) - purpose: trade  
- **Solid**: Ships with solid cargo storage
- **Liquid**: Ships with liquid cargo storage

## Update System
- **Automatic Check**: Checks for updates on startup
- **Manual Check**: Help → Check for Updates...
- **User Control**: Choose to download, skip, or ignore updates
- **GitHub Releases**: Updates distributed via GitHub

## Version Information
- **Version**: 0.1.3 Alpha
- **Release Date**: October 28, 2025
- **Ships**: 166 pilotable ships (59 non-ships excluded)
- **Engines**: 100 ship engines (17 non-ship engines excluded)
- **Dependencies**: Now includes matplotlib for visual charts

## Author
- **Developer**: @jongreg288
- **GitHub**: https://github.com/jongreg288/X4_Ship_Parse
- **Credits**: Made with the help of Claude, through Copilot

## Support
- **Issues**: Report bugs on GitHub Issues
- **Updates**: Automatic via built-in update checker
- **Data**: Supports latest X4: Foundations XML format

## License
Open source project - see repository for license details.

---

**Note**: This is an alpha release. Please report any issues you encounter!