from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFormLayout, QTabWidget,
    QMainWindow, QMenuBar, QMessageBox, QDialog, QDialogButtonBox, QGroupBox, QRadioButton,
    QSplitter, QScrollArea
)
from PyQt6.QtCore import QTimer
from .logic import compute_travel_speed
from .language_detector import language_detector
from .data_parser import refresh_text_mappings, get_current_language_info
import re
import pandas as pd

# Configure matplotlib backend before any matplotlib imports
import os
os.environ['MPLBACKEND'] = 'QtAgg'  # Set backend via environment variable

try:
    import matplotlib
    # Force backend selection 
    matplotlib.use('QtAgg', force=True)
    
    # Test that matplotlib.use actually worked
    if not hasattr(matplotlib, 'use'):
        raise AttributeError("matplotlib.use method not available")
    
    # Now safe to import matplotlib components
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
    
except (ImportError, AttributeError, RuntimeError) as e:
    # Matplotlib not available or backend failed - disable plotting features
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None
    print(f"Warning: matplotlib not available - plotting features disabled: {e}")

# Version information (network-free main application)
CURRENT_VERSION = "0.2.1 alpha"

class ShipStatsApp(QMainWindow):
    def __init__(self, ships_df, engines_df, shields_df=None, weapons_df=None, turrets_df=None):
        super().__init__()
        self.ships_df = ships_df
        self.engines_df = engines_df
        self.shields_df = shields_df if shields_df is not None else pd.DataFrame()
        self.weapons_df = weapons_df if weapons_df is not None else pd.DataFrame()
        self.turrets_df = turrets_df if turrets_df is not None else pd.DataFrame()
        # Debug info - GUI received ship data successfully
        self.init_ui()
        
        # Check for updates after a short delay (non-blocking)
        QTimer.singleShot(2000, self.check_for_updates_silent)

    def init_ui(self):
        self.setWindowTitle("X4 ShipMatrix")
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create 4 tabs
        self.comparison_tab = self.create_comparison_tab()  # New comprehensive comparison tab
        self.container_tab = self.create_ship_tab("trade", "Container Ships")
        self.solid_tab = self.create_ship_tab("solid", "Solid Cargo Ships")
        self.liquid_tab = self.create_ship_tab("liquid", "Liquid Cargo Ships")
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.comparison_tab, "Comparison")
        self.tab_widget.addTab(self.container_tab, "Container")
        self.tab_widget.addTab(self.solid_tab, "Solid")
        self.tab_widget.addTab(self.liquid_tab, "Liquid")
        
        main_layout.addWidget(self.tab_widget)
        
        central_widget.setLayout(main_layout)
    
    def create_menu_bar(self):
        """Create the menu bar with Settings and Help menus."""
        menubar = self.menuBar()
        if not menubar:
            return
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        if settings_menu:
            # Language selection action
            language_action = settings_menu.addAction('Language...')
            if language_action:
                language_action.triggered.connect(self.show_language_dialog)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        if not help_menu:
            return
        
        # Check for Updates action
        update_action = help_menu.addAction('Check for Updates...')
        if update_action:
            update_action.triggered.connect(self.check_for_updates_manual)
            
        # Visit GitHub action
        github_action = help_menu.addAction('Visit GitHub Repository...')
        if github_action:
            github_action.triggered.connect(self.open_github_page)
        
        # About action
        about_action = help_menu.addAction('About')
        if about_action:
            about_action.triggered.connect(self.show_about)
    
    def check_for_updates_silent(self):
        """Check for updates silently. Only notify for major version changes.
        Minor updates stay silent; major updates will be notified on startup.
        Use the separate X4_Updater.exe for update checking.
        """
        from pathlib import Path
        import subprocess
        
        updater_exe = Path("X4_Updater.exe")
        if updater_exe.exists():
            try:
                # Launch updater in silent mode - it will handle version-aware notifications
                subprocess.Popen([str(updater_exe), '--silent'], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass  # Silent failure - don't interrupt user experience
    def check_for_updates_manual(self):
        """Check for updates with user feedback."""
        # Launch external updater if available, otherwise show manual instructions
        from pathlib import Path
        import subprocess
        
        updater_exe = Path("X4_Updater.exe")
        if updater_exe.exists():
            try:
                subprocess.Popen([str(updater_exe)])
            except Exception:
                self.show_manual_update_instructions()
        else:
            self.show_manual_update_instructions()
    
    def show_manual_update_instructions(self):
        """Show manual update instructions."""
        QMessageBox.information(
            self,
            "Check for Updates",
            f"<h3>Manual Update Check</h3>"
            f"<p><b>Current Version:</b> {CURRENT_VERSION}</p>"
            f"<p>To check for updates, visit:</p>"
            f"<p><a href='https://github.com/jongreg288/X4_ShipMatrix/releases'>GitHub Releases</a></p>"
            f"<p>Download the latest X4 ShipMatrix.exe if a newer version is available.</p>"
        )
    
    def open_github_page(self):
        """Open the GitHub repository page in browser."""
        import webbrowser
        webbrowser.open("https://github.com/jongreg288/X4_ShipMatrix")
    
    def show_language_dialog(self):
        """Show language selection dialog."""
        dialog = LanguageSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Language was changed - refresh the data and GUI
            self.refresh_ship_names()
    
    def refresh_ship_names(self):
        """Refresh ship and engine names after language change."""
        # Force reload of text mappings
        refresh_text_mappings()
        
        # Show info about new language
        lang_info = get_current_language_info()
        QMessageBox.information(self, "Language Changed", 
                               f"Language changed to: {lang_info['language_name']}\n"
                               f"Loaded {lang_info['mapping_count']} text mappings\n\n"
                               "Note: You may need to restart the application to see "
                               "all ship names in the new language.")
    
    def show_about(self):
        """Show about dialog."""
        lang_info = get_current_language_info()
        
        QMessageBox.about(
            self,
            "About X4 ShipMatrix",
            f"""<h3>X4 ShipMatrix</h3>
            <p><b>Version:</b> {CURRENT_VERSION}</p>
            <p><b>Author:</b> @jongreg288</p>
            <p>Made with the help of Claude, through Copilot.</p>
            <p>A labor of desire to know which ship can carry the most and go the fastest.</p>
            <p><b>GitHub:</b> <a href="https://github.com/jongreg288/X4_Ship_Parse">https://github.com/jongreg288/X4_Ship_Parse</a></p>
            <hr>
            <p><b>Current Language:</b> {lang_info['language_name']}</p>
            <p><b>Text Mappings:</b> {lang_info['mapping_count']} entries</p>
            """
        )

    def extract_size_class(self, name):
        """Extract size class from ship or engine macro name.
        Examples: 
        - engine_arg_l_allround_01_mk1 -> 'l'
        - ship_arg_m_fighter_01_a -> 'm'
        - engine_tel_xl_allround_01_mk1 -> 'xl'
        """
        if not name:
            return None
        
        name_lower = str(name).lower()
        
        # Look for size pattern: _{size}_ where size is s, m, l, or xl
        # Pattern matches _s_, _m_, _l_, or _xl_ in the name
        match = re.search(r'_(xl|[sml])_', name_lower)
        if match:
            return match.group(1)
        
        return None
    
    def format_shield_name(self, macro_name):
        """
        Format shield macro name as: {faction} {size} {type} {variant}
        Example: shield_arg_m_standard_02_mk2_macro -> ARG M Standard 02 Mk2
        """
        if not macro_name:
            return macro_name
        
        # Remove 'shield_' prefix and '_macro' suffix if present
        name = macro_name.lower()
        if name.startswith('shield_'):
            name = name[7:]  # Remove 'shield_'
        if name.endswith('_macro'):
            name = name[:-6]  # Remove '_macro'
        
        # Split by underscore
        parts = name.split('_')
        
        if len(parts) < 4:
            # Not enough parts, return original
            return macro_name
        
        # Expected format: faction_size_type_number_variant
        # Example: arg_m_standard_02_mk2
        faction = parts[0].upper()
        size = parts[1].upper()
        
        # Find where the variant starts (usually mk1, mk2, mk3, or similar)
        # Type can be multiple words before the variant
        type_parts = []
        variant_parts = []
        found_variant = False
        
        for i in range(2, len(parts)):
            part = parts[i]
            # Check if this looks like a variant (mk1, mk2, etc.) or number
            if part.startswith('mk') or part.isdigit():
                found_variant = True
            
            if found_variant:
                variant_parts.append(part)
            else:
                type_parts.append(part)
        
        # Capitalize type parts
        shield_type = ' '.join(word.capitalize() for word in type_parts if not word.isdigit())
        variant = ' '.join(part.upper() if part.startswith('mk') else part for part in variant_parts)
        
        # Build final name
        result_parts = [faction, size]
        if shield_type:
            result_parts.append(shield_type)
        if variant:
            result_parts.append(variant)
        
        return ' '.join(result_parts)

    def format_engine_name(self, macro_name):
        """
        Format engine macro name as: {faction} {size} {type} {variant}
        Example: engine_arg_l_allround_01_mk3_macro -> ARG L Allround Mk3
        """
        if not macro_name:
            return macro_name
        
        # Remove 'engine_' prefix and '_macro' suffix if present
        name = macro_name.lower()
        if name.startswith('engine_'):
            name = name[7:]  # Remove 'engine_'
        if name.endswith('_macro'):
            name = name[:-6]  # Remove '_macro'
        
        # Split by underscore
        parts = name.split('_')
        
        if len(parts) < 4:
            # Not enough parts, return original
            return macro_name
        
        # Expected format: faction_size_type_number_variant
        # Example: arg_l_allround_01_mk3
        faction = parts[0].upper()
        size = parts[1].upper()
        
        # Find where the variant starts (usually mk1, mk2, mk3, or similar)
        # Type can be multiple words before the variant
        type_parts = []
        variant_parts = []
        found_variant = False
        
        for i in range(2, len(parts)):
            part = parts[i]
            # Check if this looks like a variant (mk1, mk2, etc.) or number
            if part.startswith('mk') or part.isdigit():
                found_variant = True
            
            if found_variant:
                variant_parts.append(part)
            else:
                type_parts.append(part)
        
        # Capitalize type parts
        engine_type = ' '.join(word.capitalize() for word in type_parts if not word.isdigit())
        variant = ' '.join(part.upper() if part.startswith('mk') else part for part in variant_parts)
        
        # Build final name
        result_parts = [faction, size]
        if engine_type:
            result_parts.append(engine_type)
        if variant:
            result_parts.append(variant)
        
        return ' '.join(result_parts)
    
    def analyze_shield_recommendations(self, ship_row, ship_size):
        """
        Analyze and provide detailed shield recommendations for a given ship.
        Returns dictionary with shield analysis data.
        """
        if not ship_row is not None or not ship_size:
            return None
        
        analysis = {
            'size': ship_size,
            'compatible_sizes': [],
            'faction_recommendations': [],
            'tactical_builds': [],
            'effectiveness_notes': []
        }
        
        # Size compatibility analysis
        size_hierarchy = ['s', 'm', 'l', 'xl']
        if ship_size in size_hierarchy:
            current_index = size_hierarchy.index(ship_size)
            analysis['compatible_sizes'] = size_hierarchy[:current_index + 1]
        
        # Faction-specific recommendations based on ship's maker
        maker_race = ship_row.get('maker_race', '').lower()
        hull_max = ship_row.get('hull_max', 0) if ship_row.get('hull_max') is not None else 0
        
        faction_mapping = {
            'arg': 'Argon', 'argon': 'Argon',
            'tel': 'Teladi', 'teladi': 'Teladi', 
            'par': 'Paranid', 'paranid': 'Paranid',
            'spl': 'Split', 'split': 'Split',
            'bor': 'Boron', 'boron': 'Boron',
            'ter': 'Terran', 'terran': 'Terran',
            'xen': 'Xenon', 'xenon': 'Xenon',
            'kha': 'Kha\'ak', 'khaak': 'Kha\'ak'
        }
        
        primary_faction = faction_mapping.get(maker_race, 'Universal')
        
        # Tactical build recommendations based on hull strength
        if isinstance(hull_max, (int, float)) and hull_max > 0:
            if hull_max > 15000:  # Heavy fighter
                analysis['tactical_builds'] = [
                    {'name': 'Tank Build', 'focus': 'Max capacity shields', 'color': '#28a745'},
                    {'name': 'Assault Build', 'focus': 'Balanced shields with good recharge', 'color': '#17a2b8'},
                    {'name': 'Not Recommended', 'focus': 'Fast recharge (hull can absorb damage)', 'color': '#6c757d'}
                ]
            elif hull_max > 8000:  # Medium fighter  
                analysis['tactical_builds'] = [
                    {'name': 'Balanced Build', 'focus': 'Moderate capacity with decent recharge', 'color': '#ffc107'},
                    {'name': 'Survivability Build', 'focus': 'Max capacity for tough missions', 'color': '#28a745'},
                    {'name': 'Hit-and-Run Build', 'focus': 'Fast recharge for quick recovery', 'color': '#17a2b8'}
                ]
            else:  # Light fighter
                analysis['tactical_builds'] = [
                    {'name': 'Speed Build', 'focus': 'Fast recharge, rely on mobility', 'color': '#17a2b8'},
                    {'name': 'Balanced Build', 'focus': 'Moderate protection', 'color': '#ffc107'},
                    {'name': 'High Risk', 'focus': 'Max capacity reduces maneuverability', 'color': '#dc3545'}
                ]
        
        # Effectiveness metrics
        analysis['effectiveness_notes'] = [
            'Capacity Rating: Total shield HP protection',
            'Recharge Rate: Recovery speed between hits', 
            'Delay Time: Time before recharge begins',
            'Size Efficiency: Performance vs mass/power ratio'
        ]
        
        return analysis
    
    def calculate_shield_effectiveness_rating(self, ship_row, ship_size):
        """
        Calculate shield effectiveness rating based on ship characteristics.
        Returns a dictionary with effectiveness metrics.
        """
        if not ship_row is not None or not ship_size:
            return {'overall': 0, 'details': 'No ship data available'}
        
        hull_max = ship_row.get('hull_max', 0) if ship_row.get('hull_max') is not None else 0
        mass = ship_row.get('mass', 0) if ship_row.get('mass') is not None else 0
        engine_connections = ship_row.get('engine_connections', 0) if ship_row.get('engine_connections') is not None else 0
        
        # Base effectiveness starts at 50
        effectiveness = 50
        details = []
        
        # Hull strength factor (higher hull = better shield synergy)
        if isinstance(hull_max, (int, float)) and hull_max > 0:
            if hull_max > 15000:
                effectiveness += 15
                details.append("High hull strength (+15): Excellent shield synergy")
            elif hull_max > 8000:
                effectiveness += 10
                details.append("Medium hull strength (+10): Good shield synergy") 
            else:
                effectiveness += 5
                details.append("Light hull (+5): Relies heavily on shields")
        
        # Mass efficiency factor (lower mass = better shield efficiency)
        if isinstance(mass, (int, float)) and mass > 0:
            if mass < 200:
                effectiveness += 10
                details.append("Low mass (+10): Excellent shield efficiency")
            elif mass < 500:
                effectiveness += 5
                details.append("Medium mass (+5): Good shield efficiency")
            else:
                effectiveness -= 5
                details.append("High mass (-5): Reduced shield efficiency")
        
        # Size class factor
        size_bonuses = {'s': 5, 'm': 10, 'l': 15, 'xl': 20}
        if ship_size in size_bonuses:
            bonus = size_bonuses[ship_size]
            effectiveness += bonus
            details.append(f"{ship_size.upper()}-size class (+{bonus}): Size-appropriate shields available")
        
        # Maneuverability factor (more engine connections = better shield positioning)
        if isinstance(engine_connections, (int, float)) and engine_connections > 0:
            if engine_connections >= 4:
                effectiveness += 8
                details.append("High maneuverability (+8): Excellent shield positioning")
            elif engine_connections >= 2:
                effectiveness += 5
                details.append("Good maneuverability (+5): Solid shield positioning")
            else:
                effectiveness += 2
                details.append("Basic maneuverability (+2): Limited shield positioning")
        
        # Clamp effectiveness to 0-100 range
        effectiveness = max(0, min(100, effectiveness))
        
        return {
            'overall': effectiveness,
            'details': details,
            'rating': self.get_effectiveness_rating_text(effectiveness)
        }
    
    def get_effectiveness_rating_text(self, effectiveness):
        """Convert numerical effectiveness to descriptive text."""
        if effectiveness >= 85:
            return "Excellent"
        elif effectiveness >= 70:
            return "Very Good"
        elif effectiveness >= 55:
            return "Good"
        elif effectiveness >= 40:
            return "Fair"
        else:
            return "Poor"
    
    def filter_engines_by_ship(self, tab_data):
        """Filter engine dropdown based on selected ship's size class."""
        ship_dropdown = tab_data['ship_dropdown']
        engine_dropdown = tab_data['engine_dropdown']
        ship_name_mapping = tab_data['ship_name_mapping']
        all_engine_items = tab_data.get('all_engine_items', [])
        all_engine_mapping = tab_data.get('all_engine_mapping', {})
        
        # Safety check: if we don't have the full engine data, don't filter
        if not all_engine_items or not all_engine_mapping:
            return
        
        ship_name = ship_dropdown.currentText()
        
        # If "None" is selected or empty, show all engines
        if not ship_name or ship_name == "None":
            engine_dropdown.blockSignals(True)  # Prevent recursive updates
            current_engine = engine_dropdown.currentText()
            engine_dropdown.clear()
            engine_dropdown.addItems(all_engine_items)
            # Try to restore previous selection
            index = engine_dropdown.findText(current_engine)
            if index >= 0:
                engine_dropdown.setCurrentIndex(index)
            engine_dropdown.blockSignals(False)
            return
        
        # Get ship's size class
        macro_name = ship_name_mapping.get(ship_name, ship_name)
        ship_size = self.extract_size_class(macro_name)
        
        if not ship_size:
            # Can't determine size, show all engines
            engine_dropdown.blockSignals(True)
            current_engine = engine_dropdown.currentText()
            engine_dropdown.clear()
            engine_dropdown.addItems(all_engine_items)
            index = engine_dropdown.findText(current_engine)
            if index >= 0:
                engine_dropdown.setCurrentIndex(index)
            engine_dropdown.blockSignals(False)
            return
        
        # Filter engines to matching size
        filtered_engine_items = ["None"]
        for engine_name in all_engine_items[1:]:  # Skip the first "None"
            engine_macro = all_engine_mapping.get(engine_name, engine_name)
            engine_size = self.extract_size_class(engine_macro)
            
            if engine_size == ship_size:
                filtered_engine_items.append(engine_name)
        
        # Update engine dropdown
        engine_dropdown.blockSignals(True)  # Prevent recursive updates
        current_engine = engine_dropdown.currentText()
        engine_dropdown.clear()
        engine_dropdown.addItems(filtered_engine_items)
        
        # Try to restore previous selection if it's still in the filtered list
        index = engine_dropdown.findText(current_engine)
        if index >= 0:
            engine_dropdown.setCurrentIndex(index)
        else:
            engine_dropdown.setCurrentIndex(0)  # Reset to "None"
        
        engine_dropdown.blockSignals(False)
    
    def filter_ships_by_engine(self, tab_data):
        """Filter ship dropdown based on selected engine's size class."""
        # Note: Ships are already filtered by cargo type, so we're not implementing
        # ship filtering by engine size as it would require re-filtering the base list.
        # The main use case is filtering engines by ship, which is more intuitive.
        # This method is a placeholder for future enhancement if needed.
        pass

    def filter_shields_by_ship(self, tab_data):
        """Filter shield dropdown based on selected ship's shield hardpoints and size class."""
        # Only apply shield filtering to fighter tabs
        if tab_data.get('cargo_filter') != 'fight':
            return
            
        if self.shields_df.empty:
            return
            
        ship_dropdown = tab_data['ship_dropdown']
        shield_dropdown = tab_data.get('shield_dropdown')
        shield_name_mapping = tab_data.get('shield_name_mapping', {})
        ship_name_mapping = tab_data['ship_name_mapping']
        filtered_ships = tab_data['filtered_ships']
        
        if not shield_dropdown or not shield_name_mapping:
            return
        
        ship_name = ship_dropdown.currentText()
        
        # If "None" is selected or empty, show all shields
        if not ship_name or ship_name == "None":
            shield_dropdown.blockSignals(True)
            current_shield = shield_dropdown.currentText()
            shield_dropdown.clear()
            
            # Rebuild full shield list
            shield_items = ["None"]
            for _, row in self.shields_df.iterrows():
                macro_name = row.get('name', 'Unknown')
                display_name = row.get('display_name', '')
                formatted_name = self.format_shield_name(macro_name)
                
                if formatted_name and formatted_name != macro_name:
                    clean_name = formatted_name
                elif display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                    clean_name = display_name
                else:
                    clean_name = macro_name
                
                shield_items.append(clean_name)
            
            shield_dropdown.addItems(shield_items)
            
            # Try to restore previous selection
            index = shield_dropdown.findText(current_shield)
            if index >= 0:
                shield_dropdown.setCurrentIndex(index)
            shield_dropdown.blockSignals(False)
            return
        
        # Get ship's shield compatibility info
        macro_name = ship_name_mapping.get(ship_name, ship_name)
        matched = filtered_ships[filtered_ships["macro_name"] == macro_name]
        
        if matched.empty:
            return
            
        ship_row = matched.iloc[0]
        ship_size = self.extract_size_class(macro_name)
        shield_connections = ship_row.get('shield_connections', 0)
        shield_size_class = ship_row.get('shield_size_class', None)
        
        if not ship_size or shield_connections == 0:
            # Ship has no shield hardpoints, show only "None"
            shield_dropdown.blockSignals(True)
            shield_dropdown.clear()
            shield_dropdown.addItems(["None"])
            shield_dropdown.blockSignals(False)
            return
        
        # Filter shields to compatible size class
        target_size = shield_size_class or ship_size
        filtered_shield_items = ["None"]
        
        for _, row in self.shields_df.iterrows():
            macro_name = row.get('name', 'Unknown')
            shield_size = row.get('shield_size', None)
            
            # Check if shield size matches ship's shield size requirement
            if shield_size == target_size:
                display_name = row.get('display_name', '')
                formatted_name = self.format_shield_name(macro_name)
                
                if formatted_name and formatted_name != macro_name:
                    clean_name = formatted_name
                elif display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                    clean_name = display_name
                else:
                    clean_name = macro_name
                
                filtered_shield_items.append(clean_name)
        
        # Update shield dropdown
        shield_dropdown.blockSignals(True)
        current_shield = shield_dropdown.currentText()
        shield_dropdown.clear()
        shield_dropdown.addItems(filtered_shield_items)
        
        # Try to restore previous selection if it's still in the filtered list
        index = shield_dropdown.findText(current_shield)
        if index >= 0:
            shield_dropdown.setCurrentIndex(index)
        else:
            shield_dropdown.setCurrentIndex(0)  # Reset to "None"
        
        shield_dropdown.blockSignals(False)
    
    def create_comparison_tab(self):
        """Create the comprehensive comparison tab with side panel and detailed stats."""
        from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QSplitter, QScrollArea, QGroupBox
        from PyQt6.QtCore import Qt
        
        # Main widget for the tab
        tab_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Create splitter for side panel and main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side panel for component selection
        side_panel = self.create_component_selection_panel()
        side_panel.setMinimumWidth(300)
        side_panel.setMaximumWidth(400)
        
        # Right main content area for ship stats and comparison
        main_content = self.create_main_comparison_content()
        
        # Add panels to splitter
        splitter.addWidget(side_panel)
        splitter.addWidget(main_content)
        splitter.setSizes([350, 1000])  # Default sizes
        
        main_layout.addWidget(splitter)
        tab_widget.setLayout(main_layout)
        
        return tab_widget
    
    def create_component_selection_panel(self):
        """Create the side panel with all component selection dropdowns."""
        from PyQt6.QtWidgets import QScrollArea, QGroupBox, QVBoxLayout, QFormLayout
        
        # Create scroll area for the panel
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Ship Selection Group
        ship_group = QGroupBox("Ship Selection")
        ship_layout = QFormLayout()
        
        # Ship dropdown (all ships, no restrictions)
        ship_dropdown = QComboBox()
        ship_items = ["None"]
        ship_name_mapping = {}
        
        # Add ALL ships regardless of type
        for _, row in self.ships_df.iterrows():
            display_name = row.get('display_name', '')
            macro_name = row.get('macro_name', 'Unknown')
            name_ref = row.get('name_ref', '')
            
            if display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                clean_name = display_name
            elif name_ref:
                clean_name = f"Text Ref: {name_ref}"
            else:
                clean_name = macro_name
            
            ship_items.append(clean_name)
            ship_name_mapping[clean_name] = macro_name
        
        ship_dropdown.addItems(ship_items)
        ship_layout.addRow("Ship:", ship_dropdown)
        
        # Size Filter
        size_filter = QComboBox()
        size_filter.addItems(["All Sizes", "S", "M", "L", "XL"])
        ship_layout.addRow("Size Filter:", size_filter)
        
        # Type Filter  
        type_filter = QComboBox()
        ship_types = ["All Types"] + sorted(self.ships_df['ship_type'].dropna().unique())
        type_filter.addItems(ship_types)
        ship_layout.addRow("Type Filter:", type_filter)
        
        ship_group.setLayout(ship_layout)
        scroll_layout.addWidget(ship_group)
        
        # Component Selection Groups
        # Engine Group
        engine_group = QGroupBox("Engine")
        engine_layout = QFormLayout()
        engine_dropdown = QComboBox()
        engine_dropdown.addItems(["None"])  # Will be populated based on ship selection
        engine_layout.addRow("Engine:", engine_dropdown)
        engine_group.setLayout(engine_layout)
        scroll_layout.addWidget(engine_group)
        
        # Shield Group
        shield_group = QGroupBox("Shields")
        shield_layout = QVBoxLayout()
        shield_dropdown = QComboBox()
        shield_dropdown.addItems(["None"])
        shield_layout.addWidget(shield_dropdown)
        shield_group.setLayout(shield_layout)
        scroll_layout.addWidget(shield_group)
        
        # Weapons Group
        weapons_group = QGroupBox("Primary Weapons")
        weapons_layout = QVBoxLayout()
        
        # Add weapon selection with multi-select capability
        weapons_dropdown = QComboBox()
        weapons_dropdown.addItems(["None"])
        weapons_layout.addWidget(QLabel("Weapon 1:"))
        weapons_layout.addWidget(weapons_dropdown)
        
        # Add second weapon slot
        weapons_dropdown_2 = QComboBox()
        weapons_dropdown_2.addItems(["None"])
        weapons_layout.addWidget(QLabel("Weapon 2:"))
        weapons_layout.addWidget(weapons_dropdown_2)
        
        weapons_group.setLayout(weapons_layout)
        scroll_layout.addWidget(weapons_group)
        
        # Turrets Group
        turrets_group = QGroupBox("Turrets")
        turrets_layout = QVBoxLayout()
        
        # Add turret selection slots
        turret_dropdown_1 = QComboBox()
        turret_dropdown_1.addItems(["None"])
        turrets_layout.addWidget(QLabel("Turret Slot 1:"))
        turrets_layout.addWidget(turret_dropdown_1)
        
        turret_dropdown_2 = QComboBox()
        turret_dropdown_2.addItems(["None"])
        turrets_layout.addWidget(QLabel("Turret Slot 2:"))
        turrets_layout.addWidget(turret_dropdown_2)
        
        turret_dropdown_3 = QComboBox()
        turret_dropdown_3.addItems(["None"])
        turrets_layout.addWidget(QLabel("Turret Slot 3:"))
        turrets_layout.addWidget(turret_dropdown_3)
        
        turrets_group.setLayout(turrets_layout)
        scroll_layout.addWidget(turrets_group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        # Store references for later use
        self.comparison_ship_dropdown = ship_dropdown
        self.comparison_ship_mapping = ship_name_mapping
        self.comparison_size_filter = size_filter
        self.comparison_type_filter = type_filter
        self.comparison_engine_dropdown = engine_dropdown
        self.comparison_shield_dropdown = shield_dropdown
        self.comparison_weapons_dropdown = weapons_dropdown
        self.comparison_weapons_dropdown_2 = weapons_dropdown_2
        self.comparison_turret_dropdown_1 = turret_dropdown_1
        self.comparison_turret_dropdown_2 = turret_dropdown_2
        self.comparison_turret_dropdown_3 = turret_dropdown_3
        
        # Connect signals for filtering and updates
        ship_dropdown.currentIndexChanged.connect(self.update_comparison_display)
        size_filter.currentIndexChanged.connect(self.filter_ships_by_size)
        type_filter.currentIndexChanged.connect(self.filter_ships_by_type)
        
        # Connect engine and shield selection changes
        engine_dropdown.currentIndexChanged.connect(self.update_comparison_display)
        shield_dropdown.currentIndexChanged.connect(self.update_comparison_display)
        
        # Connect weapon and turret selection changes
        weapons_dropdown.currentIndexChanged.connect(self.update_comparison_display)
        weapons_dropdown_2.currentIndexChanged.connect(self.update_comparison_display)
        turret_dropdown_1.currentIndexChanged.connect(self.update_comparison_display)
        turret_dropdown_2.currentIndexChanged.connect(self.update_comparison_display)
        turret_dropdown_3.currentIndexChanged.connect(self.update_comparison_display)
        
        return scroll_area
    
    def create_main_comparison_content(self):
        """Create the main content area for ship stats and comparison."""
        from PyQt6.QtWidgets import QScrollArea, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel
        
        # Create scroll area for main content
        scroll_area = QScrollArea()
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        
        # Ship Stats Section
        ship_stats_group = QGroupBox("Ship Statistics")
        ship_stats_layout = QVBoxLayout()
        
        ship_stats_label = QLabel("Select a ship to view detailed statistics")
        ship_stats_label.setWordWrap(True)
        ship_stats_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #444444;
                border-radius: 8px;
                font-size: 12px;
            }
        """)
        
        ship_stats_layout.addWidget(ship_stats_label)
        ship_stats_group.setLayout(ship_stats_layout)
        content_layout.addWidget(ship_stats_group)
        
        # Weapons Section
        weapons_group = QGroupBox("Weapons & Combat")
        weapons_layout = QVBoxLayout()
        
        weapons_label = QLabel("Select a ship to view weapon statistics")
        weapons_label.setWordWrap(True)
        weapons_label.setStyleSheet("""
            QLabel {
                padding: 20px;
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #444444;
                border-radius: 8px;
                font-size: 12px;
            }
        """)
        
        weapons_layout.addWidget(weapons_label)
        weapons_group.setLayout(weapons_layout)
        content_layout.addWidget(weapons_group)
        
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        
        # Store references
        self.comparison_ship_stats_label = ship_stats_label
        self.comparison_weapons_label = weapons_label
        
        return scroll_area
    
    def create_ship_tab(self, cargo_filter, tab_name):
        """Create a tab with ship selection and stats for a specific cargo type."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter ships based on purpose or cargo type
        if cargo_filter == "fight":
            # Filter for ships with purpose primary="fight" and combat ship types
            # Include all combat-oriented ship types found in the data
            combat_types = ['fighter', 'heavyfighter', 'interceptor', 'bomber', 'destroyer', 
                          'corvette', 'frigate', 'gunboat', 'scout', 'carrier', 'battleship', 'scavenger']
            filtered_ships = self.ships_df[
                (self.ships_df['purpose_primary'] == 'fight') &
                (self.ships_df['ship_type'].isin(combat_types) | self.ships_df['ship_type'].isna())
            ]
        elif cargo_filter == "trade":
            # Filter for ships with purpose primary="trade"
            filtered_ships = self.ships_df[
                self.ships_df['purpose_primary'] == 'trade'
            ]
        elif cargo_filter == "solid":
            filtered_ships = self.ships_df[
                self.ships_df['storage_cargo_type'].str.contains('solid', na=False, case=False)
            ]
        elif cargo_filter == "liquid":
            filtered_ships = self.ships_df[
                self.ships_df['storage_cargo_type'].str.contains('liquid', na=False, case=False)
            ]
        else:
            filtered_ships = self.ships_df
        
        # Create ship dropdown
        ship_dropdown = QComboBox()
        ship_items = ["None"]
        ship_name_mapping = {}
        
        for _, row in filtered_ships.iterrows():
            display_name = row.get('display_name', row.get('macro_name', 'Unknown'))
            macro_name = row.get('macro_name', 'Unknown')
            
            # Use display name if available and different from macro, otherwise use macro name
            if display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                clean_name = display_name
            else:
                clean_name = macro_name
            
            ship_items.append(clean_name)
            ship_name_mapping[clean_name] = macro_name
        
        ship_dropdown.addItems(ship_items)
        # Tooltips removed - moved to Help menu
        
        # Create engine dropdown (exclude XS engines)
        engine_dropdown = QComboBox()
        engine_items = ["None"]
        engine_name_mapping = {}
        
        for _, row in self.engines_df.iterrows():
            macro_name = row.get('name', 'Unknown')
            macro_lower = macro_name.lower()
            
            # Skip non-ship engines: XS, missiles, mines, drones, spacesuits, etc.
            if (    '_xs_' in macro_lower or 
                    'missile' in macro_lower or 
                    'mine' in macro_lower or 
                    'torpedo' in macro_lower or 
                    'drone' in macro_lower or 
                    'escapepod' in macro_lower or 
                    'police' in macro_lower or
                    'spacesuit' in macro_lower):
                continue
                
            display_name = row.get('display_name', macro_name)
            
            # Format engine name as: faction size type variant
            formatted_name = self.format_engine_name(macro_name)
            
            # Use formatted name if we successfully parsed it, otherwise fall back to display name or macro
            if formatted_name and formatted_name != macro_name:
                clean_name = formatted_name
            elif display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                clean_name = display_name
            else:
                clean_name = macro_name
            
            engine_items.append(clean_name)
            engine_name_mapping[clean_name] = macro_name
        
        engine_dropdown.addItems(engine_items)
        
        # Engine tooltips removed - moved to Help menu
        
        # Create stats label
        if cargo_filter == "fight":
            stats_label = QLabel(f"Select a fighter and engine to see combat stats.")
        else:
            stats_label = QLabel(f"Select a {cargo_filter} ship and engine to see stats.")
        
        # Store references for this tab
        tab_data = {
            'ship_dropdown': ship_dropdown,
            'engine_dropdown': engine_dropdown,
            'stats_label': stats_label,
            'ship_name_mapping': ship_name_mapping,
            'engine_name_mapping': engine_name_mapping,
            'filtered_ships': filtered_ships,
            'cargo_filter': cargo_filter,
            'all_engines': self.engines_df.copy(),  # Store all engines for filtering
            'all_engine_items': list(engine_items),  # Store all engine display names (make explicit copy)
            'all_engine_mapping': dict(engine_name_mapping)  # Store all engine mappings (make explicit copy)
        }
        
        # Connect signals for cascading filters (connect AFTER initial setup to avoid premature filtering)
        ship_dropdown.currentIndexChanged.connect(lambda: self.filter_engines_by_ship(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.filter_ships_by_engine(tab_data))
        
        # Connect signals for stats updates
        ship_dropdown.currentIndexChanged.connect(lambda: self.update_tab_stats(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_tab_stats(tab_data))
        
        # Create form layout
        form = QFormLayout()
        form.addRow("Ship:", ship_dropdown)
        form.addRow("Engine:", engine_dropdown)
        
        layout.addLayout(form)
        layout.addWidget(stats_label)
        
        # Add appropriate chart section based on tab type
        if cargo_filter == "fight":
            # Fighters get their own specialized chart section
            self.add_fighters_chart_section(layout, tab_data)
        else:
            # Cargo ships use the standard cargo/speed comparison chart
            self.add_cargo_chart_section(layout, tab_data)
        
        tab_widget.setLayout(layout)
        
        # Store tab data as attribute
        setattr(self, f'{cargo_filter}_tab_data', tab_data)
        
        return tab_widget

    def create_comparison_chart(self):
        """Create a matplotlib chart widget for cargo ship comparison.
        Used only by cargo tabs when matplotlib is available."""
        if not MATPLOTLIB_AVAILABLE or Figure is None or FigureCanvas is None:
            # This should not happen since add_cargo_chart_section checks MATPLOTLIB_AVAILABLE
            placeholder = QLabel("Chart functionality requires matplotlib")
            placeholder.setMinimumHeight(300)
            return placeholder
        
        figure = Figure(figsize=(8, 4))
        figure.patch.set_facecolor('#B3B3B3')  # 70% grey background
        canvas = FigureCanvas(figure)
        canvas.setMinimumHeight(300)
        return canvas
    # TODO:
        # "Fighters" tab - COMPLETED: shields dropdown ✅
        # REMAINING: weapons, thrusters dropdowns needed.
            # Shield files are shown as {shield} {faction} {size} {"standard"} {type} {variant}
                # Internal <macro name="shield_arg_m_standard_02_mk2_macro" class="shieldgenerator">
                # e.g. name="shield_arg_m_standard_02_mk2_macro" = "ARG M Standard 02 Mk2" ✅ IMPLEMENTED
            # Weapon files are shown as {weapon} {faction} {size} {type_01} {type_02} {variant}
                # Internal <macro name="turret_arg_m_plasma_01_mk1_macro" class="turret" alias="turret_arg_m_plasma_02_mk1_macro">
                    # If alias is present, use that for stats lookup and display
                # e.g. name="turret_arg_m_plasma_01_mk1_macro" = "Argon M Plasma 01 Mk1"
            # Thruster files are shown as {thruster} {faction} {size} {type_01} {type_02} {variant}
                # Internal <macro name="thruster_gen_m_allround_01_mk3_macro" class="engine">
                # e.g. name="thruster_gen_m_allround_01_mk3_macro" = "Generic M Allround 01 Mk3"
        # These will be used to compute fighter loadout stats and performance.
        # Will need to parse shield, weapon, and thruster data from XML files.
        # Will need to check name resolution for these parts as well, file C:\Users\pheno\Code_Projects\X4_ShipMatrix\data\t\0001-l044.xml for English.
        # Likely uses similar text mapping approach as ships and engines.
    def add_fighters_chart_section(self, layout, tab_data):
        """Add specialized fighter sub-tabbed analysis section."""
        ship_dropdown = tab_data['ship_dropdown']
        engine_dropdown = tab_data['engine_dropdown']
        
        # Create sub-tab widget for different fighter analysis views
        fighter_analysis_tabs = QTabWidget()
        
        # TAB 1: DEFENSIVE LOADOUT
        defensive_tab = QWidget()
        defensive_layout = QVBoxLayout()
        
        # Shield Analysis Section
        shield_section = QGroupBox("Shield Loadout Analysis")
        shield_layout = QVBoxLayout()
        
        # Shield selection dropdown with actual shield data
        shield_selection_layout = QFormLayout()
        shield_dropdown = QComboBox()
        
        # Populate shield dropdown with actual shield data
        shield_items = ["None"]
        shield_name_mapping = {}
        
        if not self.shields_df.empty:
            for _, row in self.shields_df.iterrows():
                macro_name = row.get('name', 'Unknown')
                display_name = row.get('display_name', '')
                
                # Format shield name as: faction size type variant
                formatted_name = self.format_shield_name(macro_name)
                
                # Use formatted name if we successfully parsed it, otherwise fall back to display name or macro
                if formatted_name and formatted_name != macro_name:
                    clean_name = formatted_name
                elif display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                    clean_name = display_name
                else:
                    clean_name = macro_name
                
                shield_items.append(clean_name)
                shield_name_mapping[clean_name] = macro_name
        
        shield_dropdown.addItems(shield_items)
        shield_dropdown.setEnabled(True)  # Enable shield selection
        shield_selection_layout.addRow("Shield:", shield_dropdown)
        shield_layout.addLayout(shield_selection_layout)
        
        # Shield compatibility and analysis display
        shield_stats_label = QLabel("Select a fighter to view shield compatibility and recommendations")
        shield_stats_label.setWordWrap(True)
        shield_stats_label.setStyleSheet("padding: 10px; background-color: #B3B3B3; color: black; border: 1px solid #666666; border-radius: 4px;")
        shield_layout.addWidget(shield_stats_label)
        shield_section.setLayout(shield_layout)
        
        defensive_layout.addWidget(shield_section)
        defensive_tab.setLayout(defensive_layout)
        
        # TAB 2: PERFORMANCE METRICS
        performance_tab = QWidget()
        performance_layout = QVBoxLayout()
        
        # Speed Analysis Section
        speed_section = QGroupBox("Speed & Maneuverability")
        speed_layout = QVBoxLayout()
        
        # Speed metrics display
        speed_stats_label = QLabel("Select a fighter and engine to view comprehensive speed analysis")
        speed_stats_label.setWordWrap(True)
        speed_stats_label.setStyleSheet("padding: 10px; background-color: #B3B3B3; color: black; border: 1px solid #666666; border-radius: 4px;")
        speed_layout.addWidget(speed_stats_label)
        speed_section.setLayout(speed_layout)
        
        # Engine Efficiency Section
        engine_section = QGroupBox("Engine Performance")
        engine_layout = QVBoxLayout()
        
        # Engine efficiency display
        engine_stats_label = QLabel("Select a fighter and engine to view engine efficiency metrics")
        engine_stats_label.setWordWrap(True)
        engine_stats_label.setStyleSheet("padding: 10px; background-color: #B3B3B3; color: black; border: 1px solid #666666; border-radius: 4px;")
        engine_layout.addWidget(engine_stats_label)
        engine_section.setLayout(engine_layout)
        
        performance_layout.addWidget(speed_section)
        performance_layout.addWidget(engine_section)
        performance_tab.setLayout(performance_layout)
        
        # TAB 3: OFFENSIVE LOADOUT (Placeholder)
        offensive_tab = QWidget()
        offensive_layout = QVBoxLayout()
        offensive_placeholder = QLabel("Offensive analysis will be implemented later.\nThis will show weapon hardpoints and combat effectiveness.")
        offensive_placeholder.setStyleSheet("padding: 20px; text-align: center; color: #666;")
        from PyQt6.QtCore import Qt
        offensive_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        offensive_layout.addWidget(offensive_placeholder)
        offensive_tab.setLayout(offensive_layout)
        
        # TAB 4: COMPARISON OVERVIEW
        overview_tab = QWidget()
        overview_layout = QVBoxLayout()
        
        # Role Suitability Section
        role_section = QGroupBox("Role Analysis")
        role_layout = QVBoxLayout()
        
        # Role analysis display
        role_stats_label = QLabel("Select a fighter and engine to view role suitability analysis")
        role_stats_label.setWordWrap(True)
        role_stats_label.setStyleSheet("padding: 10px; background-color: #B3B3B3; color: black; border: 1px solid #666666; border-radius: 4px;")
        role_layout.addWidget(role_stats_label)
        role_section.setLayout(role_layout)
        
        # Overall Assessment Section
        rating_section = QGroupBox("Overall Assessment")
        rating_layout = QVBoxLayout()
        
        # Overall rating display
        rating_stats_label = QLabel("Select a fighter and engine to view comprehensive assessment")
        rating_stats_label.setWordWrap(True)
        rating_stats_label.setStyleSheet("padding: 10px; background-color: #B3B3B3; color: black; border: 1px solid #666666; border-radius: 4px;")
        rating_layout.addWidget(rating_stats_label)
        rating_section.setLayout(rating_layout)
        
        overview_layout.addWidget(role_section)
        overview_layout.addWidget(rating_section)
        overview_tab.setLayout(overview_layout)
        
        # Add all tabs to fighter analysis
        fighter_analysis_tabs.addTab(defensive_tab, "Defense")
        fighter_analysis_tabs.addTab(performance_tab, "Performance") 
        fighter_analysis_tabs.addTab(offensive_tab, "Offense")
        fighter_analysis_tabs.addTab(overview_tab, "Overview")
        
        layout.addWidget(QLabel("<b>Fighter Analysis</b>"))
        layout.addWidget(fighter_analysis_tabs)
        
        # Store references for updates
        tab_data['chart_canvas'] = fighter_analysis_tabs
        tab_data['chart_type'] = 'fighters'
        tab_data['shield_dropdown'] = shield_dropdown
        tab_data['shield_name_mapping'] = shield_name_mapping
        tab_data['shield_stats_label'] = shield_stats_label
        tab_data['speed_stats_label'] = speed_stats_label
        tab_data['engine_stats_label'] = engine_stats_label
        tab_data['role_stats_label'] = role_stats_label
        tab_data['rating_stats_label'] = rating_stats_label
        
        # Connect signals for fighter tab updates
        ship_dropdown.currentIndexChanged.connect(lambda: self.filter_shields_by_ship(tab_data))
        ship_dropdown.currentIndexChanged.connect(lambda: self.update_fighter_defense_tab(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_fighter_defense_tab(tab_data))
        ship_dropdown.currentIndexChanged.connect(lambda: self.update_fighter_performance_tab(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_fighter_performance_tab(tab_data))
        ship_dropdown.currentIndexChanged.connect(lambda: self.update_fighter_overview_tab(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_fighter_overview_tab(tab_data))

    def add_cargo_chart_section(self, layout, tab_data):
        """Add standard cargo/speed comparison chart section for cargo ships."""
        ship_dropdown = tab_data['ship_dropdown']
        engine_dropdown = tab_data['engine_dropdown']
        
        # Only add chart functionality if matplotlib is available
        if MATPLOTLIB_AVAILABLE:
            # Connect signals for chart updates
            ship_dropdown.currentIndexChanged.connect(lambda: self.update_comparison_chart(tab_data))
            engine_dropdown.currentIndexChanged.connect(lambda: self.update_comparison_chart(tab_data))
            
            # Create matplotlib chart for comparison
            chart_canvas = self.create_comparison_chart()
            
            layout.addWidget(QLabel("<b>Cargo/Speed Comparison (Top 5 Ships)</b>"))
            layout.addWidget(chart_canvas)
            
            # Store chart canvas in tab_data for updates
            tab_data['chart_canvas'] = chart_canvas
        else:
            # Show a message when matplotlib is not available
            chart_label = QLabel("<b>Cargo/Speed Comparison</b>")
            chart_placeholder = QLabel("Chart functionality requires matplotlib.\nInstall matplotlib to enable cargo/speed comparison charts.")
            chart_placeholder.setMinimumHeight(150)
            chart_placeholder.setStyleSheet(
                "background-color: #fff3cd; "
                "border: 2px solid #ffeaa7; "
                "padding: 20px; "
                "text-align: center; "
                "color: #856404;"
            )
            from PyQt6.QtCore import Qt
            chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            layout.addWidget(chart_label)
            layout.addWidget(chart_placeholder)
            
            # Store placeholder in tab_data
            tab_data['chart_canvas'] = chart_placeholder
        
        tab_data['chart_type'] = 'cargo'
    
    def update_comparison_chart(self, tab_data):
        """Update the comparison chart with top 5 ships of same size using same engine."""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        chart_canvas = tab_data.get('chart_canvas')
        if not chart_canvas:
            return
            
        ship_dropdown = tab_data['ship_dropdown']
        engine_dropdown = tab_data['engine_dropdown']
        ship_name_mapping = tab_data['ship_name_mapping']
        engine_name_mapping = tab_data['engine_name_mapping']
        filtered_ships = tab_data['filtered_ships']
        
        ship_name = ship_dropdown.currentText()
        engine_name = engine_dropdown.currentText()
        
        # Clear the figure
        figure = chart_canvas.figure
        figure.clear()
        
        # If no valid selection, show empty chart
        if not ship_name or ship_name == "None" or not engine_name or engine_name == "None":
            ax = figure.add_subplot(111)
            ax.set_facecolor('#B3B3B3')  # 70% grey background
            ax.text(0.5, 0.5, 'Select a ship and engine to view comparison', 
                   ha='center', va='center', fontsize=12, color='black')
            ax.set_xticks([])
            ax.set_yticks([])
            chart_canvas.draw()
            return
        
        # Get the selected ship's size class
        ship_macro = ship_name_mapping.get(ship_name, ship_name)
        ship_size = self.extract_size_class(ship_macro)
        
        if not ship_size:
            ax = figure.add_subplot(111)
            ax.set_facecolor('#B3B3B3')  # 70% grey background
            ax.text(0.5, 0.5, 'Unable to determine ship size', 
                   ha='center', va='center', fontsize=12, color='black')
            ax.set_xticks([])
            ax.set_yticks([])
            chart_canvas.draw()
            return
        
        # Get the selected engine macro
        engine_macro = engine_name_mapping.get(engine_name, engine_name)
        
        # Find all ships of the same size in this tab's filtered ships
        same_size_ships = []
        for _, row in filtered_ships.iterrows():
            macro_name = row.get('macro_name', '')
            row_size = self.extract_size_class(macro_name)
            if row_size == ship_size:
                same_size_ships.append(row)
        
        # Calculate cargo/speed ratio for each ship with the selected engine
        ship_ratios = []
        for ship_row in same_size_ships:
            # Get engine data
            engine_row = self.engines_df[self.engines_df['name'] == engine_macro]
            if engine_row.empty:
                continue
            engine_row = engine_row.iloc[0]
            
            # Calculate travel speed based on 1,000,000 units of cargo over 50,000 units distance. Result is in time units. Lower is better.
            travel_speed = compute_travel_speed(ship_row, engine_row)
            storage_cargo_max = ship_row.get('storage_cargo_max', 0)
            
            if travel_speed and travel_speed > 0 and storage_cargo_max > 0:
                ratio = ((1000000 / storage_cargo_max) * (50000 / travel_speed)) / 60 * 2  # Convert to minutes with round trip factor
                display_name = ship_row.get('display_name', ship_row.get('macro_name', 'Unknown'))
                macro_name = ship_row.get('macro_name', 'Unknown')
                
                # Use display name if valid
                if display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                    label = display_name
                else:
                    label = macro_name
                
                ship_ratios.append({
                    'name': label,
                    'ratio': ratio,
                    'is_selected': (ship_row.get('macro_name') == ship_macro)
                })
        
        # Sort by ratio (ascending - lower is better) and take top 5
        ship_ratios.sort(key=lambda x: x['ratio'], reverse=False)
        top_ships = ship_ratios[:5]
        
        if not top_ships:
            ax = figure.add_subplot(111)
            ax.set_facecolor('#B3B3B3')  # 70% grey background
            ax.text(0.5, 0.5, 'No comparable ships found', 
                   ha='center', va='center', fontsize=12, color='black')
            ax.set_xticks([])
            ax.set_yticks([])
            chart_canvas.draw()
            return
        
        # Create bar chart
        ax = figure.add_subplot(111)
        ax.set_facecolor('#B3B3B3')  # 70% grey subplot background
        names = [s['name'][:30] + '...' if len(s['name']) > 30 else s['name'] for s in top_ships]
        ratios = [s['ratio'] for s in top_ships]
        colors = ['#4CAF50' if s['is_selected'] else '#2196F3' for s in top_ships]
        
        bars = ax.barh(names, ratios, color=colors)
        ax.set_xlabel('Round Trip Time: 1M Cargo over 50K Distance (Lower is Better)', fontsize=9, color='black')
        ax.set_title(f'Top 5 {ship_size.upper()}-Size Ships with {engine_name}', fontsize=11, color='black')
        ax.grid(axis='x', alpha=0.5, color='white')
        
        # Style the axes for better visibility on grey background
        ax.tick_params(colors='black', which='both')
        ax.spines['bottom'].set_color('black')
        ax.spines['left'].set_color('black')
        ax.spines['top'].set_color('black')
        ax.spines['right'].set_color('black')
        
        # Add value labels on bars
        for i, (bar, ratio) in enumerate(zip(bars, ratios)):
            ax.text(ratio, bar.get_y() + bar.get_height()/2, 
                   f' {ratio:.2f}', va='center', fontsize=9, color='black')
        
        figure.tight_layout()
        chart_canvas.draw()

    def update_tab_stats(self, tab_data):
        ship_dropdown = tab_data['ship_dropdown']
        engine_dropdown = tab_data['engine_dropdown']
        stats_label = tab_data['stats_label']
        ship_name_mapping = tab_data['ship_name_mapping']
        engine_name_mapping = tab_data['engine_name_mapping']
        filtered_ships = tab_data['filtered_ships']
        
        ship_name = ship_dropdown.currentText()
        engine_name = engine_dropdown.currentText()

        # Resolve selected rows; allow 'None' selection which maps to None
        if ship_name == "None":
            ship_row = None
        else:
            # Use the mapping to get the macro name from the clean display name
            macro_name = ship_name_mapping.get(ship_name, ship_name)
            matched = filtered_ships[filtered_ships["macro_name"] == macro_name]
            ship_row = matched.iloc[0] if not matched.empty else None

        if engine_name == "None":
            engine_row = None
        else:
            # Use the mapping to get the macro name from the clean display name
            engine_macro_name = engine_name_mapping.get(engine_name, engine_name)
            matched_eng = self.engines_df[self.engines_df["name"] == engine_macro_name]
            engine_row = matched_eng.iloc[0] if not matched_eng.empty else None

        travel_speed = compute_travel_speed(ship_row, engine_row)

        if ship_row is not None:
            display_name = ship_row.get('display_name', '')
            macro_name = ship_row.get('macro_name', 'None')
            if display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                ship_display = f"{display_name}"
            else:
                ship_display = macro_name
        else:
            ship_display = 'None'
        hull = ship_row.get('hull_max', 'N/A') if ship_row is not None else 'N/A'
        storage_cargo_max = ship_row.get('storage_cargo_max', 0) if ship_row is not None else 0
        storage_cargo_type = ship_row.get('storage_cargo_type', 'N/A') if ship_row is not None else 'N/A'
        
        if engine_row is not None:
            engine_display_name = engine_row.get('display_name', '')
            engine_macro_name = engine_row.get('name', 'None')
            if engine_display_name and engine_display_name != engine_macro_name and not engine_display_name.startswith("Text Ref:"):
                engine_display = engine_display_name
            else:
                engine_display = engine_macro_name
        else:
            engine_display = 'None'

        if travel_speed is None:
            travel_speed_display = "N/A"
        else:
            travel_speed_display = f"{travel_speed:.1f}"

        # Check if this is a fighter tab to show different stats
        cargo_filter = tab_data.get('cargo_filter', '')
        
        if cargo_filter == "fight":
            # Fighter-specific display - no cargo information
            
            # Get fighter-specific data
            mass = ship_row.get('mass', 'N/A') if ship_row is not None else 'N/A'
            engine_connections = ship_row.get('engine_connections', 'N/A') if ship_row is not None else 'N/A'
            shield_connections = ship_row.get('shield_connections', 'N/A') if ship_row is not None else 'N/A'
                        
            text = (
                f"<b>Fighter:</b> {ship_display}<br>"
                f"<b>Role:</b> {(ship_row.get('ship_type') or 'N/A').capitalize() if ship_row is not None else 'N/A'}<br>"
                f"<b>Hull Integrity:</b> {hull}<br>"
                f"<b>Mass:</b> {mass}<br>"
                f"<b>Engine Hardpoints:</b> {engine_connections}<br>"
                f"<b>Shield Hardpoints:</b> {shield_connections}<br>"
                f"<b>Engine:</b> {engine_display}<br>"
                f"<b>Travel Speed:</b> {travel_speed_display} m/s<br>"
            )
        else:
            # Cargo ship display - keep existing cargo functionality
            
            # Format storage information
            if storage_cargo_max > 0 and storage_cargo_type and storage_cargo_type != 'N/A':
                storage_display = f"{storage_cargo_max:,} ({storage_cargo_type})"
            else:
                storage_display = "None"

            # Calculate cargo-to-speed ratio
            # Ratio is based off moving 1,000,000 units of cargo over 50,000 units distance (round trip). Lower is better.
            # Math: ((1,000,000 / storage_cargo_max) * (50,000 / travel_speed)) / 60 * 2 = time units for round trip
            cargo_speed_ratio = None
            if travel_speed is not None and travel_speed > 0 and storage_cargo_max > 0:
                cargo_speed_ratio = ((1000000 / storage_cargo_max) * (50000 / travel_speed)) / 60 * 2  # Convert to minutes with round trip factor
                ratio_display = f"{cargo_speed_ratio:.2f}"
            else:
                ratio_display = "N/A"

            text = (
                f"<b>Ship:</b> {ship_display}<br>"
                f"<b>Role:</b> {(ship_row.get('ship_type') or 'N/A').capitalize() if ship_row is not None else 'N/A'}<br>"
                f"<b>Hull Integrity:</b> {hull}<br>"
                f"<b>Storage:</b> {storage_display}<br>"
                f"<b>Engine:</b> {engine_display}<br>"
                f"<b>Travel Speed:</b> {travel_speed_display}<br>"
                f"<b>Cargo/Speed Ratio:</b> {ratio_display}"
            )
        stats_label.setText(text)
        stats_label.setWordWrap(True)  # Enable word wrap for better display
        
        # Tooltip updates removed - moved to Help menu

    def update_tab_detailed_tooltip(self, tab_data, ship_row, engine_row, travel_speed, storage_cargo_max, cargo_speed_ratio):
        """Update the stats label tooltip with detailed information."""
        stats_label = tab_data['stats_label']
        tooltip_parts = []
        
        if ship_row is not None:
            # Ship details
            mass = ship_row.get('mass', 'N/A')
            drag_forward = ship_row.get('drag (forward)', 'N/A')
            engine_connections = ship_row.get('engine_connections', 'N/A')
            maker_race = ship_row.get('maker_race', 'N/A')
            
            tooltip_parts.append(f"SHIP DETAILS:")
            tooltip_parts.append(f"• Maker: {maker_race}")
            tooltip_parts.append(f"• Mass: {mass}")
            tooltip_parts.append(f"• Forward Drag: {drag_forward}")
            tooltip_parts.append(f"• Engine Connections: {engine_connections}")
            
        if engine_row is not None:
            # Engine details
            travel_thrust = engine_row.get('travel_thrust', 'N/A')
            forward_thrust = engine_row.get('forward_thrust', 'N/A')
            boost_thrust = engine_row.get('boost_thrust', 'N/A')
            
            if tooltip_parts:
                tooltip_parts.append("")
            tooltip_parts.append(f"ENGINE DETAILS:")
            tooltip_parts.append(f"• Travel Thrust: {travel_thrust}")
            tooltip_parts.append(f"• Forward Thrust: {forward_thrust}")
            tooltip_parts.append(f"• Boost Thrust: {boost_thrust}")
            
        if travel_speed is not None and travel_speed > 0:
            if tooltip_parts:
                tooltip_parts.append("")
            tooltip_parts.append(f"CALCULATIONS:")
            tooltip_parts.append(f"• Travel Speed Formula: (Forward Thrust × Travel Thrust × Engine Connections) / Forward Drag")
            tooltip_parts.append(f"• Result: {travel_speed:.1f} m/s")
            
            if cargo_speed_ratio is not None:
                tooltip_parts.append(f"• Cargo/Speed Ratio: {cargo_speed_ratio:.2f} minutes")
                tooltip_parts.append(f"  → Time for round trip: 1M cargo over 50K distance")
                tooltip_parts.append(f"  → Lower values = Better overall performance")
        
        if not tooltip_parts:
            tooltip_parts.append("Select a ship and engine to see detailed information")
            
        stats_label.setToolTip("\n".join(tooltip_parts))

    def update_fighter_detailed_tooltip(self, tab_data, ship_row, engine_row, travel_speed):
        """Update the stats label tooltip with fighter-specific detailed information."""
        stats_label = tab_data['stats_label']
        tooltip_parts = []
        
        if ship_row is not None:
            # Fighter details
            mass = ship_row.get('mass', 'N/A')
            hull_max = ship_row.get('hull_max', 'N/A')
            engine_connections = ship_row.get('engine_connections', 'N/A')
            maker_race = ship_row.get('maker_race', 'N/A')
            
            tooltip_parts.append(f"SHIP DETAILS:")
            tooltip_parts.append(f"• Faction: {maker_race}")
            tooltip_parts.append(f"• Hull Integrity: {hull_max}")
            tooltip_parts.append(f"• Mass: {mass}")
            tooltip_parts.append(f"• Engine Hardpoints: {engine_connections}")
            
        if engine_row is not None:
            # Engine details
            travel_thrust = engine_row.get('travel_thrust', 'N/A')
            forward_thrust = engine_row.get('forward_thrust', 'N/A')
            boost_thrust = engine_row.get('boost_thrust', 'N/A')
            
            if tooltip_parts:
                tooltip_parts.append("")
            tooltip_parts.append(f"ENGINE PERFORMANCE:")
            tooltip_parts.append(f"• Forward Thrust: {forward_thrust}")
            tooltip_parts.append(f"• Boost Thrust: {boost_thrust}")
            tooltip_parts.append(f"• Travel Speed Formula: (Forward Thrust × Travel Thrust × Engine Connections) / Forward Drag")
            tooltip_parts.append(f"• Travel Thrust: {travel_thrust}")
            tooltip_parts.append(f"• Maximum Speed: {travel_speed:.1f} m/s")
                                
        stats_label.setToolTip("\n".join(tooltip_parts))
    
    def update_tab_ship_tooltip(self, tab_data):
        """Update ship dropdown tooltip based on current selection."""
        ship_dropdown = tab_data['ship_dropdown']
        ship_name_mapping = tab_data['ship_name_mapping']
        filtered_ships = tab_data['filtered_ships']
        cargo_filter = tab_data['cargo_filter']
        
        ship_name = ship_dropdown.currentText()
        
        if ship_name == "None":
            if cargo_filter == "fight":
                ship_dropdown.setToolTip("Select a fighter to analyze.\nFighters are combat ships optimized for speed and agility")
            else:
                ship_dropdown.setToolTip(f"Select a {cargo_filter} ship to analyze.\nShip names indicate: [faction]_[size]_[type]_[variant]")
        else:
            # Use the mapping to get the macro name from the clean display name
            macro_name = ship_name_mapping.get(ship_name, ship_name)
            
            # Find the selected ship
            matched = filtered_ships[filtered_ships["macro_name"] == macro_name]
            if not matched.empty:
                ship = matched.iloc[0]
                mass = ship.get('mass', 'N/A')
                hull = ship.get('hull_max', 'N/A')
                storage_max = ship.get('storage_cargo_max', 0)
                storage_type = ship.get('storage_cargo_type', 'N/A')
                maker = ship.get('maker_race', 'N/A')
                display_name = ship.get('display_name', macro_name)
                name_ref = ship.get('name_ref', '')
                
                if cargo_filter == "fight":
                    # Fighter-specific tooltip
                    tooltip = f"FIGHTER: {display_name}\n"
                    if name_ref:
                        tooltip += f"• Text Reference: {name_ref}\n"
                    tooltip += f"• Macro: {macro_name}\n"
                    tooltip += f"• Faction: {maker}\n"
                    tooltip += f"• Hull Integrity: {hull}\n"
                    tooltip += f"• Mass: {mass}\n"
                    tooltip += f"• Role: Combat vessel optimized for speed and firepower"
                else:
                    # Cargo ship tooltip
                    tooltip = f"SHIP: {display_name}\n"
                    if name_ref:
                        tooltip += f"• Text Reference: {name_ref}\n"
                    tooltip += f"• Macro: {macro_name}\n"
                    tooltip += f"• Faction: {maker}\n"
                    tooltip += f"• Hull: {hull}\n"
                    tooltip += f"• Mass: {mass}\n"
                    if storage_max > 0:
                        tooltip += f"• Storage: {storage_max:,} ({storage_type})"
                    else:
                        tooltip += "• Storage: None"
                
                ship_dropdown.setToolTip(tooltip)
    
    def update_tab_engine_tooltip(self, tab_data):
        """Update engine dropdown tooltip based on current selection."""
        engine_dropdown = tab_data['engine_dropdown']
        engine_name_mapping = tab_data['engine_name_mapping']
        cargo_filter = tab_data.get('cargo_filter', '')
        engine_name = engine_dropdown.currentText()
        
        if engine_name == "None":
            if cargo_filter == "fight":
                engine_dropdown.setToolTip("Select an engine to pair with the fighter.\nHigher travel thrust = better combat mobility\n(Non-ship engines excluded)")
            else:
                engine_dropdown.setToolTip("Select an engine to pair with the ship.\nHigher travel thrust = faster travel speed\n(Non-ship engines excluded)")
        else:
            # Use the mapping to get the macro name from the clean display name
            engine_macro_name = engine_name_mapping.get(engine_name, engine_name)
            
            # Find the selected engine
            matched_eng = self.engines_df[self.engines_df["name"] == engine_macro_name]
            if not matched_eng.empty:
                engine = matched_eng.iloc[0]
                travel_thrust = engine.get('travel_thrust', 'N/A')
                forward_thrust = engine.get('forward_thrust', 'N/A')
                boost_thrust = engine.get('boost_thrust', 'N/A')
                display_name = engine.get('display_name', engine_macro_name)
                maker_race = engine.get('maker_race', 'N/A')
                mk = engine.get('mk', '')
                basename_ref = engine.get('basename_ref', '')
                
                tooltip = f"ENGINE: {display_name}\n"
                if basename_ref:
                    tooltip += f"• Text Reference: {basename_ref}\n"
                tooltip += f"• Macro: {engine_macro_name}\n"
                tooltip += f"• Faction: {maker_race}\n"
                if mk:
                    tooltip += f"• Mark: {mk}\n"
                tooltip += f"• Travel Thrust: {travel_thrust}\n"
                tooltip += f"• Forward Thrust: {forward_thrust}\n"
                tooltip += f"• Boost Thrust: {boost_thrust}\n"
                
                if cargo_filter == "fight":
                    tooltip += f"• Combat Performance: Higher thrust = better interceptor capability"
                else:
                    tooltip += f"• Higher travel thrust = faster travel speed"
                
                engine_dropdown.setToolTip(tooltip)

    def update_fighter_defense_tab(self, tab_data):
        """Update the Defense tab content for fighters."""
        ship_dropdown = tab_data['ship_dropdown']
        ship_name_mapping = tab_data['ship_name_mapping']
        filtered_ships = tab_data['filtered_ships']
        shield_stats_label = tab_data.get('shield_stats_label')
        
        ship_name = ship_dropdown.currentText()
        
        # Get selected ship data
        if ship_name == "None" or not ship_name:
            if shield_stats_label:
                shield_stats_label.setText("Select a fighter to view shield compatibility and recommendations")
            return
        
        # Use the mapping to get the macro name from the clean display name
        macro_name = ship_name_mapping.get(ship_name, ship_name)
        matched = filtered_ships[filtered_ships["macro_name"] == macro_name]
        
        if matched.empty:
            if shield_stats_label:
                shield_stats_label.setText("Ship data not found")
            return
        
        ship_row = matched.iloc[0]
        
        # Update Shield Analysis
        if shield_stats_label:
            ship_size = self.extract_size_class(macro_name)
            maker_race = ship_row.get('maker_race', 'Unknown')
            hull_max = ship_row.get('hull_max', 0)
            shield_connections = ship_row.get('shield_connections', 0)
            shield_size_class = ship_row.get('shield_size_class', None)
            
            if ship_size:
                shield_text = f"<b>Shield Analysis for {ship_size.upper()}-size Fighter:</b><br><br>"
                
                # Shield hardpoint information
                shield_text += f"<b>🔌 Shield Hardpoints:</b><br>"
                if shield_connections > 0:
                    shield_text += f"• <span style='color: #28a745; font-weight: bold;'>{shield_connections}</span> shield hardpoint{'s' if shield_connections != 1 else ''}<br>"
                    if shield_size_class:
                        shield_text += f"• Hardpoint size: <span style='color: #007bff; font-weight: bold;'>{shield_size_class.upper()}</span> class shields<br>"
                    
                    # Shield effectiveness multiplier based on hardpoint count
                    if shield_connections >= 2:
                        shield_text += f"• <span style='color: #28a745;'>High protection:</span> Multiple shields provide redundancy<br>"
                    else:
                        shield_text += f"• <span style='color: #ffc107;'>Standard protection:</span> Single shield hardpoint<br>"
                else:
                    shield_text += f"• <span style='color: #dc3545; font-weight: bold;'>No shield hardpoints detected</span><br>"
                    shield_text += f"• <span style='color: #dc3545;'>Warning:</span> This ship relies entirely on hull integrity<br>"
                
                shield_text += f"<br>"
                                                
                # Faction recommendations
                shield_text += f"<b>🏭 Faction Recommendations:</b><br>"
                if maker_race in ['arg', 'argon']:
                    shield_text += f"• <span style='color: #0066cc;'>Argon</span>: Balanced capacity and recharge rates<br>"
                    shield_text += f"• <span style='color: #009900;'>Teladi</span>: High capacity, slower recharge<br>"
                    shield_text += f"• <span style='color: #ff6600;'>Paranid</span>: Fast recharge, lower capacity<br>"
                elif maker_race in ['tel', 'teladi']:
                    shield_text += f"• <span style='color: #009900;'>Teladi</span>: Superior capacity (faction bonus)<br>"
                    shield_text += f"• <span style='color: #0066cc;'>Argon</span>: Reliable alternative<br>"
                    shield_text += f"• <span style='color: #cc0000;'>Split</span>: High-energy shields<br>"
                elif maker_race in ['par', 'paranid']:
                    shield_text += f"• <span style='color: #ff6600;'>Paranid</span>: Superior recharge (faction bonus)<br>"
                    shield_text += f"• <span style='color: #0066cc;'>Argon</span>: Balanced option<br>"
                    shield_text += f"• <span style='color: #009900;'>Teladi</span>: High capacity shields<br>"
                elif maker_race in ['spl', 'split']:
                    shield_text += f"• <span style='color: #cc0000;'>Split</span>: High-energy shields (faction bonus)<br>"
                    shield_text += f"• <span style='color: #0066cc;'>Argon</span>: Reliable standard<br>"
                    shield_text += f"• <span style='color: #ff6600;'>Paranid</span>: Fast recharge<br>"
                elif maker_race in ['bor', 'boron']:
                    shield_text += f"• <span style='color: #0077cc;'>Boron</span>: Advanced shielding technology<br>"
                    shield_text += f"• <span style='color: #0066cc;'>Argon</span>: Reliable standard<br>"
                    shield_text += f"• <span style='color: #ff6600;'>Paranid</span>: Fast recharge<br>"
                elif maker_race in ['ter', 'terran']:
                    shield_text += f"• <span style='color: #336699;'>Terran</span>: Earth military-grade technology (faction bonus)<br>"
                    shield_text += f"• <span style='color: #0066cc;'>Argon</span>: Compatible Commonwealth tech<br>"
                    shield_text += f"• <span style='color: #009900;'>Teladi</span>: High capacity alternative<br>"
                else:
                    shield_text += f"• <span style='color: #0066cc;'>Argon</span>: Balanced choice<br>"
                    shield_text += f"• <span style='color: #009900;'>Teladi</span>: High capacity<br>"
                    shield_text += f"• <span style='color: #ff6600;'>Paranid</span>: Fast recharge<br>"

                shield_text += f"<br>"
                
                # Tactical loadout recommendations based on hull strength
                shield_text += f"<b>⚔️ Tactical Loadout Recommendations:</b><br>"
                if isinstance(hull_max, (int, float)) and hull_max > 0:
                    if ship_size == 'xl':  # Capital Class
                        shield_text += f"• <span style='color: #474747;'>XL Shields do not have a recharge delay.</span><br>"
                        shield_text += f"• <span style='color: #811212;'>Strike Build</span>: Max capacity shields for short engagements<br>"
                        shield_text += f"• <span style='color: #0b6e12;'>Balanced Build</span>: Balanced shields builders or fleet supply vessels<br>"
                        shield_text += f"• <span style='color: #0b1e6e;'>Tank Build</span>: High recharge rate for prolonged engagements<br>"
                    elif ship_size == 'l':  # Destroyer Class
                        shield_text += f"• <span style='color: #474747;'>L Shields do not have a recharge delay.</span><br>"
                        shield_text += f"• <span style='color: #811212;'>Strike Build</span>: Max capacity shields for short engagements<br>"
                        shield_text += f"• <span style='color: #0b6e12;'>Balanced Build</span>: Balanced shields for transporters or miners<br>"
                        shield_text += f"• <span style='color: #0b1e6e;'>Tank Build</span>: High recharge rate for prolonged engagements<br>"
                    elif ship_size == 'm':  # Frigate Class
                        shield_text += f"• <span style='color: #811212;'>Capacity</span>: <br>"
                        shield_text += f"• <span style='color: #0b6e12;'>Recharge Rate</span>: <br>"
                        shield_text += f"• <span style='color: #0b1e6e;'>Recharge Delay</span>: <br>"
                    else:  # Fighter and Scout Class
                        shield_text += f"• <span style='color: #811212;'>Capacity</span>: <br>"
                        shield_text += f"• <span style='color: #0b6e12;'>Recharge Rate</span>: <br>"
                        shield_text += f"• <span style='color: #0b1e6e;'>Recharge Delay</span>: <br>"
                else:
                    shield_text += f"• Standard tactical builds available<br>"
                    shield_text += f"• Capacity vs Recharge trade-offs apply<br>"
                
                shield_text += f"<br>"
                                
                # Advanced shield metrics
                shield_text += f"<b>📈 Shield Performance Metrics:</b><br>"
                shield_text += f"• <i>Capacity Rating</i>: Total shield amount<br>"
                shield_text += f"• <i>Recharge Rate</i>: Recovery speed between hits<br>"
                shield_text += f"• <i>Delay Time</i>: Time before recharge begins<br>"
            else:
                shield_text = "Unable to determine fighter size class for shield compatibility"
            
            shield_stats_label.setText(shield_text)

    def update_fighter_performance_tab(self, tab_data):
        """Update the Performance tab content for fighters."""
        ship_dropdown = tab_data['ship_dropdown']
        engine_dropdown = tab_data['engine_dropdown']
        ship_name_mapping = tab_data['ship_name_mapping']
        engine_name_mapping = tab_data['engine_name_mapping']
        filtered_ships = tab_data['filtered_ships']
        speed_stats_label = tab_data.get('speed_stats_label')
        engine_stats_label = tab_data.get('engine_stats_label')
        
        ship_name = ship_dropdown.currentText()
        engine_name = engine_dropdown.currentText()
        
        # Check for valid selections
        if ship_name == "None" or not ship_name:
            if speed_stats_label:
                speed_stats_label.setText("Select a fighter to view comprehensive speed analysis")
            if engine_stats_label:
                speed_stats_label.setText("Select a fighter and engine to view engine efficiency metrics")
            return
        
        if engine_name == "None" or not engine_name:
            if speed_stats_label:
                speed_stats_label.setText("Select an engine to view speed analysis")
            if engine_stats_label:
                engine_stats_label.setText("Select an engine to view engine efficiency metrics")
            return
        
        # Get ship and engine data
        ship_macro = ship_name_mapping.get(ship_name, ship_name)
        engine_macro = engine_name_mapping.get(engine_name, engine_name)
        
        ship_matched = filtered_ships[filtered_ships["macro_name"] == ship_macro]
        engine_matched = self.engines_df[self.engines_df["name"] == engine_macro]
        
        if ship_matched.empty or engine_matched.empty:
            if speed_stats_label:
                speed_stats_label.setText("Ship or engine data not found")
            if engine_stats_label:
                engine_stats_label.setText("Ship or engine data not found")
            return
        
        ship_row = ship_matched.iloc[0]
        engine_row = engine_matched.iloc[0]
        
        # Calculate performance metrics
        travel_speed = compute_travel_speed(ship_row, engine_row)
        
        # Update Speed Analysis
        if speed_stats_label:
            speed_text = f"<b>Speed & Maneuverability Analysis:</b><br><br>"
            
            if travel_speed and travel_speed > 0:
                speed_text += f"<b>Travel Speed:</b> {travel_speed:.1f} m/s<br><br>"
                
                # Speed rating for fighters
                if travel_speed >= 300:
                    speed_rating = "<span style='color: #28a745;'>Excellent</span> - Fast interceptor"
                elif travel_speed >= 200:
                    speed_rating = "<span style='color: #ffc107;'>Good</span> - Standard fighter speed"
                elif travel_speed >= 150:
                    speed_rating = "<span style='color: #fd7e14;'>Average</span> - Moderate speed"
                else:
                    speed_rating = "<span style='color: #dc3545;'>Slow</span> - Heavy fighter"
                
                speed_text += f"<b>Speed Rating:</b> {speed_rating}<br><br>"
            else:
                speed_text += f"<b>Travel Speed:</b> Unable to calculate<br><br>"
            
            # Additional speed metrics (placeholders for future enhancement)
            speed_text += f"<b>Additional Metrics:</b><br>"
            speed_text += f"• <i>Boost Speed:</i> Data not available<br>"
            speed_text += f"• <i>Boost Duration:</i> Data not available<br>"
            speed_text += f"• <i>Turn Rates:</i> Data not available<br>"
            speed_text += f"• <i>Acceleration:</i> Data not available<br><br>"
            speed_text += f"<i>Enhanced speed metrics will be added in future updates</i>"
            
            speed_stats_label.setText(speed_text)
        
        # Update Engine Efficiency
        if engine_stats_label:
            mass = ship_row.get('mass', 'N/A')
            travel_thrust = engine_row.get('travel_thrust', 'N/A')
            forward_thrust = engine_row.get('forward_thrust', 'N/A')
            boost_thrust = engine_row.get('boost_thrust', 'N/A')
            engine_connections = ship_row.get('engine_connections', 'N/A')
            
            engine_text = f"<b>Engine Performance Analysis:</b><br><br>"
            engine_text += f"<b>Engine Specifications:</b><br>"
            engine_text += f"• Travel Thrust: {travel_thrust}<br>"
            engine_text += f"• Forward Thrust: {forward_thrust}<br>"
            engine_text += f"• Boost Thrust: {boost_thrust}<br><br>"
            
            engine_text += f"<b>Ship Integration:</b><br>"
            engine_text += f"• Engine Connections: {engine_connections}<br>"
            engine_text += f"• Ship Mass: {mass}<br><br>"
            
            # Calculate thrust-to-weight ratio if we have the data
            if (isinstance(forward_thrust, (int, float)) and forward_thrust > 0 and
                isinstance(mass, (int, float)) and mass > 0 and
                isinstance(engine_connections, (int, float)) and engine_connections > 0):
                
                total_thrust = forward_thrust * engine_connections
                thrust_to_weight = total_thrust / mass
                engine_text += f"<b>Thrust-to-Weight Ratio:</b> {thrust_to_weight:.2f}<br>"
                
                # Efficiency rating
                if thrust_to_weight >= 15:
                    efficiency_rating = "<span style='color: #28a745;'>Excellent</span> - High acceleration"
                elif thrust_to_weight >= 10:
                    efficiency_rating = "<span style='color: #ffc107;'>Good</span> - Standard acceleration"
                elif thrust_to_weight >= 5:
                    efficiency_rating = "<span style='color: #fd7e14;'>Average</span> - Moderate acceleration"
                else:
                    efficiency_rating = "<span style='color: #dc3545;'>Poor</span> - Sluggish acceleration"
                
                engine_text += f"<b>Efficiency Rating:</b> {efficiency_rating}<br><br>"
                
                # Calculate estimated speeds (X4 physics approximations)
                travel_speed = self.estimate_travel_speed(travel_thrust, mass, engine_connections)
                max_speed = self.estimate_max_speed(forward_thrust, mass, engine_connections)
                boost_speed = self.estimate_boost_speed(boost_thrust, mass, engine_connections)
                
                engine_text += f"<b>Speed Performance Metrics:</b><br>"
                engine_text += self.create_speed_performance_bars(travel_speed, max_speed, boost_speed)
                
                # Performance comparison rating
                performance_rating = self.calculate_engine_performance_rating(thrust_to_weight, travel_speed, max_speed)
                engine_text += f"<br><b>Overall Performance:</b> {performance_rating}<br>"
                
            else:
                engine_text += f"<b>Thrust-to-Weight Ratio:</b> Unable to calculate<br><br>"
                engine_text += f"<b>Performance Analysis:</b> Insufficient data for calculation<br>"
            
            engine_stats_label.setText(engine_text)

    def update_fighter_overview_tab(self, tab_data):
        """Update the Overview tab content with role analysis and overall assessment."""
        ship_dropdown = tab_data['ship_dropdown']
        engine_dropdown = tab_data['engine_dropdown']
        ship_name_mapping = tab_data['ship_name_mapping']
        engine_name_mapping = tab_data['engine_name_mapping']
        filtered_ships = tab_data['filtered_ships']
        role_stats_label = tab_data.get('role_stats_label')
        rating_stats_label = tab_data.get('rating_stats_label')
        
        ship_name = ship_dropdown.currentText()
        engine_name = engine_dropdown.currentText()
        
        # Check for valid selections
        if ship_name == "None" or not ship_name or engine_name == "None" or not engine_name:
            if role_stats_label:
                role_stats_label.setText("Select a fighter and engine to view role suitability analysis")
            if rating_stats_label:
                rating_stats_label.setText("Select a fighter and engine to view comprehensive assessment")
            return
        
        # Get ship and engine data
        ship_macro = ship_name_mapping.get(ship_name, ship_name)
        engine_macro = engine_name_mapping.get(engine_name, engine_name)
        
        ship_matched = filtered_ships[filtered_ships["macro_name"] == ship_macro]
        engine_matched = self.engines_df[self.engines_df["name"] == engine_macro]
        
        if ship_matched.empty or engine_matched.empty:
            if role_stats_label:
                role_stats_label.setText("Ship or engine data not found")
            if rating_stats_label:
                rating_stats_label.setText("Ship or engine data not found")
            return
        
        ship_row = ship_matched.iloc[0]
        engine_row = engine_matched.iloc[0]
        
        # Calculate metrics for role analysis
        travel_speed = compute_travel_speed(ship_row, engine_row)
        hull_max = ship_row.get('hull_max', 0)
        mass = ship_row.get('mass', 0)
        
        # Initialize role scores (needed for both role analysis and overall assessment)
        interceptor_score = 0
        assault_score = 0
        multi_role_score = 0
        
        # Update Role Analysis
        if role_stats_label:
            role_text = f"<b>Fighter Role Suitability Analysis:</b><br><br>"
            
            # Speed contributes to interceptor role
            if travel_speed and travel_speed > 0:
                if travel_speed >= 300:
                    interceptor_score += 3
                    multi_role_score += 2
                elif travel_speed >= 200:
                    interceptor_score += 2
                    multi_role_score += 2
                    assault_score += 1
                elif travel_speed >= 150:
                    interceptor_score += 1
                    multi_role_score += 2
                    assault_score += 2
                else:
                    assault_score += 3
                    multi_role_score += 1
            
            # Hull contributes to assault role
            if isinstance(hull_max, (int, float)) and hull_max > 0:
                if hull_max >= 5000:
                    assault_score += 3
                    multi_role_score += 2
                elif hull_max >= 2000:
                    assault_score += 2
                    multi_role_score += 3
                    interceptor_score += 1
                else:
                    interceptor_score += 3
                    multi_role_score += 1
            
            # Calculate role percentages
            total_score = max(interceptor_score + assault_score + multi_role_score, 1)
            interceptor_pct = (interceptor_score / total_score) * 100
            assault_pct = (assault_score / total_score) * 100
            multi_role_pct = (multi_role_score / total_score) * 100
            
            role_text += f"<b>Role Ratings:</b><br>"
            role_text += f"• <b>Interceptor:</b> <span style='color: #17a2b8;'>{interceptor_pct:.0f}%</span> (Speed + Agility focus)<br>"
            role_text += f"• <b>Assault Fighter:</b> <span style='color: #dc3545;'>{assault_pct:.0f}%</span> (Durability + Firepower focus)<br>"
            role_text += f"• <b>Multi-role:</b> <span style='color: #28a745;'>{multi_role_pct:.0f}%</span> (Balanced performance)<br><br>"
            
            # Determine best role
            if interceptor_score >= assault_score and interceptor_score >= multi_role_score:
                best_role = "<span style='color: #17a2b8;'><b>Interceptor</b></span>"
                role_desc = "Best suited for fast hit-and-run attacks, pursuit, and patrol missions"
            elif assault_score >= multi_role_score:
                best_role = "<span style='color: #dc3545;'><b>Assault Fighter</b></span>"
                role_desc = "Best suited for direct combat, escort duties, and sustained engagements"
            else:
                best_role = "<span style='color: #28a745;'><b>Multi-role Fighter</b></span>"
                role_desc = "Best suited for versatile missions requiring balanced capabilities"
            
            role_text += f"<b>Primary Role:</b> {best_role}<br>"
            role_text += f"<b>Mission Profile:</b> {role_desc}"
            
            role_stats_label.setText(role_text)
        
        # Update Overall Assessment
        if rating_stats_label:
            rating_text = f"<b>Comprehensive Fighter Assessment:</b><br><br>"
            
            # Collect strengths and weaknesses
            strengths = []
            weaknesses = []
            
            if travel_speed and travel_speed > 0:
                if travel_speed >= 300:
                    strengths.append("Exceptional speed")
                elif travel_speed >= 200:
                    strengths.append("Good speed")
                elif travel_speed < 150:
                    weaknesses.append("Limited speed")
            
            if isinstance(hull_max, (int, float)) and hull_max > 0:
                if hull_max >= 5000:
                    strengths.append("High survivability")
                elif hull_max >= 2000:
                    strengths.append("Adequate durability")
                else:
                    weaknesses.append("Low hull integrity")
            
            # Calculate overall effectiveness (0-100)
            effectiveness = 50  # Base score
            
            if travel_speed and travel_speed > 0:
                speed_bonus = min((travel_speed - 100) / 10, 25)  # Up to +25 for speed
                effectiveness += max(speed_bonus, 0)
            
            if isinstance(hull_max, (int, float)) and hull_max > 0:
                hull_bonus = min((hull_max - 1000) / 200, 25)  # Up to +25 for hull
                effectiveness += max(hull_bonus, 0)
            
            effectiveness = max(0, min(100, effectiveness))  # Clamp to 0-100
            
            # Effectiveness rating
            if effectiveness >= 85:
                eff_color = "#28a745"
                eff_grade = "Excellent"
            elif effectiveness >= 70:
                eff_color = "#17a2b8"
                eff_grade = "Very Good"
            elif effectiveness >= 55:
                eff_color = "#ffc107"
                eff_grade = "Good"
            elif effectiveness >= 40:
                eff_color = "#fd7e14"
                eff_grade = "Average"
            else:
                eff_color = "#dc3545"
                eff_grade = "Below Average"
            
            rating_text += f"<b>Overall Effectiveness:</b> <span style='color: {eff_color};'>{effectiveness:.0f}/100 ({eff_grade})</span><br><br>"
            
            if strengths:
                rating_text += f"<b>Key Strengths:</b><br>"
                for strength in strengths:
                    rating_text += f"• <span style='color: #28a745;'>{strength}</span><br>"
                rating_text += "<br>"
            
            if weaknesses:
                rating_text += f"<b>Areas of Concern:</b><br>"
                for weakness in weaknesses:
                    rating_text += f"• <span style='color: #dc3545;'>{weakness}</span><br>"
                rating_text += "<br>"
            
            rating_text += f"<b>Recommended Use Cases:</b><br>"
            if interceptor_score >= assault_score and interceptor_score >= multi_role_score:
                rating_text += f"• Fast response missions<br>• Reconnaissance and patrol<br>• Hit-and-run attacks"
            elif assault_score >= multi_role_score:
                rating_text += f"• Direct combat engagements<br>• Capital ship escort<br>• Defense operations"
            else:
                rating_text += f"• General purpose missions<br>• Flexible deployment<br>• Mixed fleet operations"
            
            rating_stats_label.setText(rating_text)

    def update_comparison_display(self):
        """Update the main comparison display when ship selection changes."""
        ship_name = self.comparison_ship_dropdown.currentText()
        
        if ship_name == "None" or not ship_name:
            self.comparison_ship_stats_label.setText("Select a ship to view detailed statistics")
            self.comparison_weapons_label.setText("Select a ship to view weapon statistics")
            return
        
        # Get ship data
        macro_name = self.comparison_ship_mapping.get(ship_name, ship_name)
        matched = self.ships_df[self.ships_df["macro_name"] == macro_name]
        
        if matched.empty:
            self.comparison_ship_stats_label.setText("Ship data not found")
            self.comparison_weapons_label.setText("Ship data not found")
            return
        
        ship_row = matched.iloc[0]
        
        # Update ship stats display
        self.update_ship_stats_display(ship_row)
        
        # Update weapons display  
        self.update_weapons_display(ship_row)
        
        # Update component dropdowns based on ship compatibility
        self.update_component_dropdowns(ship_row)
    
    def update_ship_stats_display(self, ship_row):
        """Update the ship statistics section with comprehensive data."""
        # Get basic ship info
        display_name = ship_row.get('display_name', '') or ship_row.get('macro_name', 'Unknown')
        ship_type = (ship_row.get('ship_type') or 'Unknown').capitalize()
        maker_race_raw = ship_row.get('maker_race', 'Unknown')
        maker_race = str(maker_race_raw).capitalize() if maker_race_raw is not None else 'Unknown'
        
        # Ship statistics as requested
        hull = ship_row.get('hull_max', 'N/A')
        shield_connections = ship_row.get('shield_connections', 0)
        mass = ship_row.get('mass', 'N/A')
        
        # Flight performance data
        drag_forward = ship_row.get('drag (forward)', 'N/A')
        drag_reverse = ship_row.get('drag (reverse)', 'N/A')
        
        # Build comprehensive stats display
        stats_html = f"""
        <div style='color: white; font-family: Arial, sans-serif;'>
            <h2 style='color: #4CAF50; border-bottom: 2px solid #4CAF50; padding-bottom: 5px;'>
                {display_name}
            </h2>
            
            <h3 style='color: #2196F3; margin-top: 20px;'>Ship Information</h3>
            {self.create_ship_info_bars(ship_row)}
            <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
                <tr><td style='padding: 3px 10px; color: #BBB;'>Type:</td><td style='padding: 3px 10px; color: #4CAF50; font-weight: bold;'>{ship_type}</td></tr>
                <tr><td style='padding: 3px 10px; color: #BBB;'>Faction:</td><td style='padding: 3px 10px; color: #2196F3; font-weight: bold;'>{maker_race}</td></tr>
                <tr><td style='padding: 3px 10px; color: #BBB;'>Mass:</td><td style='padding: 3px 10px; color: #FF9800; font-weight: bold;'>{mass}</td></tr>
            </table>
            
            <h3 style='color: #2196F3; margin-top: 20px;'>Defensive Systems</h3>
            {self.create_defensive_stats_bars(hull, shield_connections)}
            <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
                <tr><td style='padding: 3px 10px; color: #BBB;'>Hull Integrity:</td><td style='padding: 3px 10px; color: #4CAF50; font-weight: bold;'>{hull}</td></tr>
                <tr><td style='padding: 3px 10px; color: #BBB;'>Shield Hardpoints:</td><td style='padding: 3px 10px; color: #2196F3; font-weight: bold;'>{shield_connections}</td></tr>
            </table>
            
            <h3 style='color: #2196F3; margin-top: 20px;'>Flight Performance</h3>
            <table style='width: 100%; border-collapse: collapse;'>
                <tr><td style='padding: 3px 10px; color: #BBB;'>Forward Drag:</td><td style='padding: 3px 10px;'>{drag_forward}</td></tr>
                <tr><td style='padding: 3px 10px; color: #BBB;'>Reverse Drag:</td><td style='padding: 3px 10px;'>{drag_reverse}</td></tr>
            </table>
            
            <p style='color: #888; font-size: 10px; margin-top: 20px;'>
                Note: Additional flight performance data will be calculated when engine is selected.
            </p>
        </div>
        """
        
        self.comparison_ship_stats_label.setText(stats_html)
    
    def update_weapons_display(self, ship_row):
        """Update the weapons statistics section."""
        # Get selected weapons and turrets
        selected_weapons = []
        selected_turrets = []
        
        # Get selected weapons
        weapon1_text = self.comparison_weapons_dropdown.currentText()
        if weapon1_text and weapon1_text != "None":
            selected_weapons.append(weapon1_text)
        
        weapon2_text = self.comparison_weapons_dropdown_2.currentText()
        if weapon2_text and weapon2_text != "None":
            selected_weapons.append(weapon2_text)
        
        # Get selected turrets
        for turret_dropdown in [self.comparison_turret_dropdown_1, self.comparison_turret_dropdown_2, self.comparison_turret_dropdown_3]:
            turret_text = turret_dropdown.currentText()
            if turret_text and turret_text != "None":
                selected_turrets.append(turret_text)
        
        weapons_html = f"""
        <div style='color: white; font-family: Arial, sans-serif;'>
            <h2 style='color: #FF9800; border-bottom: 2px solid #FF9800; padding-bottom: 5px;'>
                Weapons & Combat
            </h2>
            
            <h3 style='color: #F44336; margin-top: 20px;'>Primary Weapons</h3>
        """
        
        if selected_weapons:
            for i, weapon in enumerate(selected_weapons, 1):
                weapons_html += f"<p style='color: #4CAF50;'>Slot {i}: {weapon}</p>"
        else:
            weapons_html += "<p style='color: #BBB;'>No weapons selected</p>"
        
        weapons_html += "<h3 style='color: #F44336; margin-top: 20px;'>Turrets</h3>"
        
        if selected_turrets:
            for i, turret in enumerate(selected_turrets, 1):
                weapons_html += f"<p style='color: #4CAF50;'>Turret {i}: {turret}</p>"
        else:
            weapons_html += "<p style='color: #BBB;'>No turrets selected</p>"
        
        # Calculate performance metrics
        combat_stats = self.calculate_combat_performance(ship_row, selected_weapons, selected_turrets)
        
        # Display performance based on available data
        if combat_stats['has_performance_data']:
            weapons_html += f"""
                <h3 style='color: #2196F3; margin-top: 20px;'>Combat Performance</h3>
                <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
                    <tr><td style='padding: 3px 10px; color: #BBB;'>Total DPS:</td><td style='padding: 3px 10px; color: #4CAF50;'>{combat_stats['total_dps']:.1f}</td></tr>
                    <tr><td style='padding: 3px 10px; color: #BBB;'>Max Range:</td><td style='padding: 3px 10px; color: #2196F3;'>{combat_stats['max_range']:.0f}m</td></tr>
                    <tr><td style='padding: 3px 10px; color: #BBB;'>Weapon Count:</td><td style='padding: 3px 10px;'>{combat_stats['weapon_count']}</td></tr>
                    <tr><td style='padding: 3px 10px; color: #BBB;'>Turret Count:</td><td style='padding: 3px 10px;'>{combat_stats['turret_count']}</td></tr>
                </table>
            """
        else:
            weapons_html += f"""
                <h3 style='color: #2196F3; margin-top: 20px;'>Combat Overview</h3>
                <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
                    <tr><td style='padding: 3px 10px; color: #BBB;'>Weapon Count:</td><td style='padding: 3px 10px; color: #4CAF50;'>{combat_stats['weapon_count']}</td></tr>
                    <tr><td style='padding: 3px 10px; color: #BBB;'>Turret Count:</td><td style='padding: 3px 10px; color: #2196F3;'>{combat_stats['turret_count']}</td></tr>
                    <tr><td style='padding: 3px 10px; color: #BBB;'>Total Hardpoints:</td><td style='padding: 3px 10px;'>{combat_stats['weapon_count'] + combat_stats['turret_count']}</td></tr>
                </table>
                <p style='color: #FFC107; font-size: 11px; margin-top: 10px;'>
                    ⚠️ Detailed DPS calculations require enhanced weapon data
                </p>
            """
            
        weapons_html += f"""
            <h3 style='color: #2196F3; margin-top: 20px;'>Combat Rating</h3>
            <div style='background: #333; padding: 10px; border-radius: 5px; margin-top: 10px;'>
                <div style='color: {combat_stats['rating_color']}; font-size: 16px; font-weight: bold; margin-bottom: 8px;'>
                    {combat_stats['rating_text']} ({combat_stats['rating_score']}/100)
                </div>
                
                <!-- Enhanced Visual Progress Bar -->
                <div style='position: relative; width: 100%; background: #555; height: 24px; border-radius: 12px; overflow: hidden; border: 2px solid #444;'>
                    <!-- Gradient Background -->
                    <div style='position: absolute; width: 100%; height: 100%; background: linear-gradient(90deg, #F44336 0%, #FF5722 25%, #FFC107 50%, #FF9800 75%, #4CAF50 100%); opacity: 0.3;'></div>
                    
                    <!-- Progress Fill with Animation Effect -->
                    <div style='position: absolute; width: {combat_stats['rating_score']}%; height: 100%; background: {combat_stats['rating_color']}; border-radius: 10px; 
                                box-shadow: 0 0 10px rgba(255,255,255,0.25), inset 0 2px 4px rgba(255,255,255,0.2); 
                                transition: width 0.8s ease-in-out;'></div>
                    
                    <!-- Percentage Text Overlay -->
                    <div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                                color: white; font-weight: bold; font-size: 12px; text-shadow: 1px 1px 2px black;'>
                        {combat_stats['rating_score']}%
                    </div>
                    
                    <!-- Scale Markers -->
                    <div style='position: absolute; top: -5px; left: 25%; width: 1px; height: 8px; background: #666;'></div>
                    <div style='position: absolute; top: -5px; left: 50%; width: 1px; height: 8px; background: #666;'></div>
                    <div style='position: absolute; top: -5px; left: 75%; width: 1px; height: 8px; background: #666;'></div>
                </div>
                
                <!-- Rating Scale Labels -->
                <div style='display: flex; justify-content: space-between; margin-top: 5px; font-size: 9px; color: #888;'>
                    <span>Poor</span>
                    <span>Average</span>
                    <span>Good</span>
                    <span>Excellent</span>
                </div>
            </div>
            
            <p style='color: #888; font-size: 10px; margin-top: 20px;'>
                {"Performance calculated from detailed weapon stats" if combat_stats['has_performance_data'] else "Rating based on weapon count and configuration"}
            </p>
        </div>
        """
        
        self.comparison_weapons_label.setText(weapons_html)
    
    def update_component_dropdowns(self, ship_row):
        """Update engine, shield, weapon and turret dropdowns based on selected ship compatibility."""
        # Get ship info for compatibility
        macro_name = ship_row.get('macro_name', '')
        maker_race = ship_row.get('maker_race', 'unknown')
        ship_size = self.extract_size_class(macro_name) or 'unknown'
        
        # Update engine dropdown
        self.populate_engine_dropdown(self.comparison_engine_dropdown, ship_size, maker_race)
        
        # Update shield dropdown  
        self.populate_shield_dropdown(self.comparison_shield_dropdown, ship_size, maker_race)
        
        # Update weapons dropdowns
        self.populate_weapons_dropdown(self.comparison_weapons_dropdown, ship_size, maker_race)
        self.populate_weapons_dropdown(self.comparison_weapons_dropdown_2, ship_size, maker_race)
        
        # Update turret dropdowns
        self.populate_turrets_dropdown(self.comparison_turret_dropdown_1, ship_size, maker_race)
        self.populate_turrets_dropdown(self.comparison_turret_dropdown_2, ship_size, maker_race)
        self.populate_turrets_dropdown(self.comparison_turret_dropdown_3, ship_size, maker_race)
    
    def filter_ships_by_size(self):
        """Filter ship dropdown based on selected size."""
        size_filter = self.comparison_size_filter.currentText()
        self.apply_ship_filters()
    
    def filter_ships_by_type(self):
        """Filter ship dropdown based on selected type."""
        type_filter = self.comparison_type_filter.currentText()
        self.apply_ship_filters()
    
    def apply_ship_filters(self):
        """Apply size and type filters to ship dropdown."""
        size_filter = self.comparison_size_filter.currentText()
        type_filter = self.comparison_type_filter.currentText()
        
        # Start with all ships
        filtered_ships = self.ships_df.copy()
        
        # Apply size filter
        if size_filter != "All Sizes":
            # Extract size from macro_name (assuming format like ship_xxx_SIZE_xxx)
            filtered_ships = filtered_ships[
                filtered_ships['macro_name'].str.contains(f'_{size_filter.lower()}_', na=False)
            ]
        
        # Apply type filter
        if type_filter != "All Types":
            filtered_ships = filtered_ships[
                filtered_ships['ship_type'].str.contains(type_filter, case=False, na=False)
            ]
        
        # Update ship dropdown
        self.comparison_ship_dropdown.blockSignals(True)
        current_ship = self.comparison_ship_dropdown.currentText()
        self.comparison_ship_dropdown.clear()
        
        ship_items = ["None"]
        ship_name_mapping = {}
        
        for _, row in filtered_ships.iterrows():
            display_name = row.get('display_name', '')
            macro_name = row.get('macro_name', 'Unknown')
            name_ref = row.get('name_ref', '')
            
            if display_name and display_name != macro_name and not display_name.startswith("Text Ref:"):
                clean_name = display_name
            elif name_ref:
                clean_name = f"Text Ref: {name_ref}"
            else:
                clean_name = macro_name
            
            ship_items.append(clean_name)
            ship_name_mapping[clean_name] = macro_name
        
        self.comparison_ship_dropdown.addItems(ship_items)
        self.comparison_ship_mapping = ship_name_mapping
        
        # Try to restore previous selection
        index = self.comparison_ship_dropdown.findText(current_ship)
        if index >= 0:
            self.comparison_ship_dropdown.setCurrentIndex(index)
        else:
            self.comparison_ship_dropdown.setCurrentIndex(0)
        
        self.comparison_ship_dropdown.blockSignals(False)
        
        # Update display
        self.update_comparison_display()
    
    def populate_weapons_dropdown(self, dropdown, ship_size=None, selected_faction=None):
        """Populate weapons dropdown with compatible weapons."""
        dropdown.blockSignals(True)
        current_selection = dropdown.currentText()
        dropdown.clear()
        
        weapon_items = ["None"]
        weapon_mapping = {}  # Map formatted names to weapon data
        
        if not self.weapons_df.empty:
            # Filter weapons based on compatibility
            filtered_weapons = self.weapons_df.copy()
            
            # Advanced size compatibility filtering
            if ship_size:
                compatible_sizes = self.get_compatible_weapon_sizes(ship_size)
                filtered_weapons = filtered_weapons[filtered_weapons['size_class'].isin(compatible_sizes)]
            
            # Faction preference filtering (but don't exclude other factions entirely)
            if selected_faction and selected_faction.lower() != 'unknown':
                # Sort so faction weapons appear first, but include others
                filtered_weapons['faction_priority'] = filtered_weapons['faction'].apply(
                    lambda x: 0 if x.lower() == selected_faction.lower() else 1
                )
                filtered_weapons = filtered_weapons.sort_values(['faction_priority', 'faction', 'weapon_type', 'mk_level'])
            else:
                # Sort by faction, type, mk level
                filtered_weapons = filtered_weapons.sort_values(['faction', 'weapon_type', 'mk_level'])
            
            for _, row in filtered_weapons.iterrows():
                weapon_id = row.get('weapon_id', '')
                display_name = row.get('display_name', weapon_id)
                weapon_type = row.get('weapon_type', 'unknown')
                faction = row.get('faction', 'unknown').capitalize()
                mk_level = row.get('mk_level', 1)
                size_class = row.get('size_class', 'unknown').upper()
                
                # Create formatted name with size indicator
                type_display = weapon_type.replace('_', ' ').title()
                if display_name and display_name != weapon_id and not display_name.startswith('('):
                    # Clean display name by removing reference markers
                    clean_name = display_name.split('{')[0].strip()
                    if clean_name.startswith('(') and ')' in clean_name:
                        clean_name = clean_name.split(')', 1)[1].strip()
                    formatted_name = f"[{size_class}] {clean_name} - {faction} {type_display} Mk{mk_level}"
                else:
                    formatted_name = f"[{size_class}] {weapon_id} - {faction} {type_display} Mk{mk_level}"
                
                weapon_items.append(formatted_name)
                weapon_mapping[formatted_name] = row.to_dict()
        
        dropdown.addItems(weapon_items)
        
        # Store mapping for later use
        dropdown.weapon_mapping = weapon_mapping
        
        # Try to restore previous selection
        index = dropdown.findText(current_selection)
        if index >= 0:
            dropdown.setCurrentIndex(index)
        
        dropdown.blockSignals(False)
    
    def get_compatible_weapon_sizes(self, ship_size):
        """Get list of weapon sizes compatible with ship size."""
        ship_size_lower = ship_size.lower()
        
        # X4 weapon compatibility rules
        if ship_size_lower in ["s", "small"]:
            return ["small"]
        elif ship_size_lower in ["m", "medium"]:
            return ["small", "medium"]
        elif ship_size_lower in ["l", "large"]:
            return ["small", "medium", "large"]
        elif ship_size_lower in ["xl", "extra_large"]:
            return ["small", "medium", "large", "extra_large"]
        else:
            # Unknown size, allow all
            return ["small", "medium", "large", "extra_large"]
    
    def get_compatible_turret_sizes(self, ship_size):
        """Get list of turret sizes compatible with ship size."""
        ship_size_lower = ship_size.lower()
        
        # X4 turret compatibility rules (typically more restricted than weapons)
        if ship_size_lower in ["s", "small"]:
            return ["small"]
        elif ship_size_lower in ["m", "medium"]:
            return ["small", "medium"]
        elif ship_size_lower in ["l", "large"]:
            return ["medium", "large"]  # Large ships typically don't use small turrets
        elif ship_size_lower in ["xl", "extra_large"]:
            return ["large", "extra_large"]  # XL ships use only large+ turrets
        else:
            # Unknown size, allow all
            return ["small", "medium", "large", "extra_large"]
    
    def populate_turrets_dropdown(self, dropdown, ship_size=None, selected_faction=None):
        """Populate turrets dropdown with compatible turrets."""
        dropdown.blockSignals(True)
        current_selection = dropdown.currentText()
        dropdown.clear()
        
        turret_items = ["None"]
        turret_mapping = {}  # Map formatted names to turret data
        
        if not self.turrets_df.empty:
            # Filter turrets based on compatibility
            filtered_turrets = self.turrets_df.copy()
            
            # Advanced size compatibility filtering
            if ship_size:
                compatible_sizes = self.get_compatible_turret_sizes(ship_size)
                filtered_turrets = filtered_turrets[filtered_turrets['size_class'].isin(compatible_sizes)]
            
            # Faction preference filtering (but don't exclude other factions entirely)
            if selected_faction and selected_faction.lower() != 'unknown':
                # Sort so faction turrets appear first, but include others
                filtered_turrets['faction_priority'] = filtered_turrets['faction'].apply(
                    lambda x: 0 if x.lower() == selected_faction.lower() else 1
                )
                filtered_turrets = filtered_turrets.sort_values(['faction_priority', 'faction', 'turret_type', 'mk_level'])
            else:
                # Sort by faction, type, mk level
                filtered_turrets = filtered_turrets.sort_values(['faction', 'turret_type', 'mk_level'])
            
            for _, row in filtered_turrets.iterrows():
                turret_id = row.get('turret_id', '')
                display_name = row.get('display_name', turret_id)
                turret_type = row.get('turret_type', 'unknown')
                faction = row.get('faction', 'unknown').capitalize()
                mk_level = row.get('mk_level', 1)
                size_class = row.get('size_class', 'unknown').upper()
                
                # Create formatted name with size indicator
                type_display = turret_type.replace('_', ' ').title()
                if display_name and display_name != turret_id and not display_name.startswith('('):
                    # Clean display name by removing reference markers
                    clean_name = display_name.split('{')[0].strip()
                    if clean_name.startswith('(') and ')' in clean_name:
                        clean_name = clean_name.split(')', 1)[1].strip()
                    formatted_name = f"[{size_class}] {clean_name} - {faction} {type_display} Mk{mk_level}"
                else:
                    formatted_name = f"[{size_class}] {turret_id} - {faction} {type_display} Mk{mk_level}"
                
                turret_items.append(formatted_name)
                turret_mapping[formatted_name] = row.to_dict()
        
        dropdown.addItems(turret_items)
        
        # Store mapping for later use
        dropdown.turret_mapping = turret_mapping
        
        # Try to restore previous selection
        index = dropdown.findText(current_selection)
        if index >= 0:
            dropdown.setCurrentIndex(index)
        
        dropdown.blockSignals(False)
    
    def populate_engine_dropdown(self, dropdown, ship_size=None, selected_faction=None):
        """Populate engine dropdown with compatible engines."""
        dropdown.blockSignals(True)
        current_selection = dropdown.currentText()
        dropdown.clear()
        
        engine_items = ["None"]
        engine_mapping = {}  # Map formatted names to engine data
        
        if hasattr(self, 'engines_df') and not self.engines_df.empty:
            # Filter engines based on compatibility
            filtered_engines = self.engines_df.copy()
            
            # Size-based filtering - engines should match ship size
            if ship_size:
                size_lower = ship_size.lower()
                if size_lower in ['s', 'small']:
                    # Small ships use small engines only
                    filtered_engines = filtered_engines[
                        filtered_engines['name'].str.contains('_s_', case=False, na=False)
                    ]
                elif size_lower in ['m', 'medium']:
                    # Medium ships use medium engines only
                    filtered_engines = filtered_engines[
                        filtered_engines['name'].str.contains('_m_', case=False, na=False)
                    ]
                elif size_lower in ['l', 'large']:
                    # Large ships use large engines only
                    filtered_engines = filtered_engines[
                        filtered_engines['name'].str.contains('_l_', case=False, na=False)
                    ]
                elif size_lower in ['xl', 'extra_large']:
                    # XL ships use XL engines only
                    filtered_engines = filtered_engines[
                        filtered_engines['name'].str.contains('_xl_', case=False, na=False)
                    ]
            
            # Faction preference filtering (but don't exclude other factions entirely)
            if selected_faction and selected_faction.lower() != 'unknown':
                # Sort so faction engines appear first, but include others
                filtered_engines['faction_priority'] = filtered_engines['maker_race'].apply(
                    lambda x: 0 if x is not None and str(x).lower() == selected_faction.lower() else 1
                )
                filtered_engines = filtered_engines.sort_values(['faction_priority', 'maker_race', 'mk'])
            else:
                # Sort by faction and mk level
                filtered_engines = filtered_engines.sort_values(['maker_race', 'mk'])
            
            for _, row in filtered_engines.iterrows():
                engine_id = row.get('name', '')  # Use 'name' instead of 'macro_name'
                display_name = row.get('display_name', engine_id)
                mk_level = row.get('mk', 1)
                faction_raw = row.get('maker_race', 'unknown')
                faction = str(faction_raw).capitalize() if faction_raw is not None else 'Unknown'
                
                # Extract engine size from the engine name
                size_indicator = ""
                if '_s_' in engine_id.lower():
                    size_indicator = "[S] "
                elif '_m_' in engine_id.lower():
                    size_indicator = "[M] "
                elif '_l_' in engine_id.lower():
                    size_indicator = "[L] "
                elif '_xl_' in engine_id.lower():
                    size_indicator = "[XL] "
                
                # Create formatted name
                if display_name and display_name != engine_id and not display_name.startswith('('):
                    # Clean display name by removing reference markers
                    clean_name = display_name.split('{')[0].strip()
                    if clean_name.startswith('(') and ')' in clean_name:
                        clean_name = clean_name.split(')', 1)[1].strip()
                    formatted_name = f"{size_indicator}{clean_name} Mk{mk_level} - {faction}"
                else:
                    formatted_name = f"{size_indicator}{engine_id} Mk{mk_level} - {faction}"
                
                engine_items.append(formatted_name)
                engine_mapping[formatted_name] = row.to_dict()
        
        dropdown.addItems(engine_items)
        
        # Store mapping for later use
        dropdown.engine_mapping = engine_mapping
        
        # Try to restore previous selection
        index = dropdown.findText(current_selection)
        if index >= 0:
            dropdown.setCurrentIndex(index)
        
        dropdown.blockSignals(False)
    
    def populate_shield_dropdown(self, dropdown, ship_size=None, selected_faction=None):
        """Populate shield dropdown with compatible shields."""
        dropdown.blockSignals(True)
        current_selection = dropdown.currentText()
        dropdown.clear()
        
        shield_items = ["None"]
        shield_mapping = {}  # Map formatted names to shield data
        
        if hasattr(self, 'shields_df') and not self.shields_df.empty:
            # Filter shields based on compatibility
            filtered_shields = self.shields_df.copy()
            
            # Size-based filtering (shields have size compatibility)
            if ship_size:
                size_lower = ship_size.lower()
                if size_lower in ['s', 'small']:
                    # Small ships use small/medium shields
                    filtered_shields = filtered_shields[
                        filtered_shields['shield_size'].isin(['s', 'm'])
                    ]
                elif size_lower in ['m', 'medium']:
                    # Medium ships use small/medium/large shields
                    filtered_shields = filtered_shields[
                        filtered_shields['shield_size'].isin(['s', 'm', 'l'])
                    ]
                elif size_lower in ['l', 'large']:
                    # Large ships use medium/large/xl shields
                    filtered_shields = filtered_shields[
                        filtered_shields['shield_size'].isin(['m', 'l', 'xl'])
                    ]
                elif size_lower in ['xl', 'extra_large']:
                    # XL ships use large/xl shields
                    filtered_shields = filtered_shields[
                        filtered_shields['shield_size'].isin(['l', 'xl'])
                    ]
            
            # Faction preference filtering
            if selected_faction and selected_faction.lower() != 'unknown':
                # Sort so faction shields appear first, but include others
                filtered_shields['faction_priority'] = filtered_shields['maker_race'].apply(
                    lambda x: 0 if x is not None and str(x).lower() == selected_faction.lower() else 1
                )
                filtered_shields = filtered_shields.sort_values(['faction_priority', 'maker_race', 'mk'])
            else:
                # Sort by faction and mk level
                filtered_shields = filtered_shields.sort_values(['maker_race', 'mk'])
            
            for _, row in filtered_shields.iterrows():
                shield_id = row.get('name', '')  # Use 'name' instead of 'macro_name'
                display_name = row.get('display_name', shield_id)
                shield_size = row.get('shield_size', 'unknown')
                mk_level = row.get('mk', 1)
                faction_raw = row.get('maker_race', 'unknown')
                faction = str(faction_raw).capitalize() if faction_raw is not None else 'Unknown'
                
                # Create size indicator from shield_size
                size_indicator = f"[{shield_size.upper()}] " if shield_size != 'unknown' else ""
                
                # Create formatted name
                if display_name and display_name != shield_id and not display_name.startswith('('):
                    # Clean display name by removing reference markers
                    clean_name = display_name.split('{')[0].strip()
                    if clean_name.startswith('(') and ')' in clean_name:
                        clean_name = clean_name.split(')', 1)[1].strip()
                    formatted_name = f"{size_indicator}{clean_name} Mk{mk_level} - {faction}"
                else:
                    formatted_name = f"{size_indicator}{shield_id} Mk{mk_level} - {faction}"
                
                shield_items.append(formatted_name)
                shield_mapping[formatted_name] = row.to_dict()
        
        dropdown.addItems(shield_items)
        
        # Store mapping for later use
        dropdown.shield_mapping = shield_mapping
        
        # Try to restore previous selection
        index = dropdown.findText(current_selection)
        if index >= 0:
            dropdown.setCurrentIndex(index)
        
        dropdown.blockSignals(False)
    
    def calculate_combat_performance(self, ship_row, selected_weapons, selected_turrets):
        """Calculate comprehensive combat performance metrics"""
        
        # Initialize stats
        total_dps = 0.0
        max_range = 0.0
        weapon_count = 0
        turret_count = 0
        has_performance_data = False
        
        # Calculate weapon DPS
        if selected_weapons:
            for weapon_id in selected_weapons:
                weapon_data = self.weapons_df[self.weapons_df['weapon_id'] == weapon_id]
                if not weapon_data.empty:
                    weapon_row = weapon_data.iloc[0]
                    weapon_count += 1
                    
                    # Check if we have performance data columns
                    if 'damage' in weapon_row or 'hull_damage' in weapon_row or 'shield_damage' in weapon_row:
                        has_performance_data = True
                        # Get weapon stats
                        damage = weapon_row.get('damage', 0)
                        hull_damage = weapon_row.get('hull_damage', 0)
                        shield_damage = weapon_row.get('shield_damage', 0)
                        reload_time = weapon_row.get('reload_time', 1.0)
                        range_val = weapon_row.get('range', 0)
                        
                        # Calculate effective damage (prefer specific damage types)
                        effective_damage = max(damage or 0, hull_damage or 0, shield_damage or 0)
                        
                        # Calculate DPS (damage per second)
                        if reload_time > 0:
                            weapon_dps = effective_damage / reload_time
                            total_dps += weapon_dps
                        
                        # Track max range
                        if range_val > max_range:
                            max_range = range_val
        
        # Calculate turret DPS
        if selected_turrets:
            for turret_id in selected_turrets:
                turret_data = self.turrets_df[self.turrets_df['turret_id'] == turret_id]
                if not turret_data.empty:
                    turret_row = turret_data.iloc[0]
                    turret_count += 1
                    
                    # Check if we have performance data columns
                    if 'damage' in turret_row or 'hull_damage' in turret_row or 'shield_damage' in turret_row:
                        has_performance_data = True
                        # Get turret stats (turrets may have multiple weapons)
                        damage = turret_row.get('damage', 0)
                        hull_damage = turret_row.get('hull_damage', 0)
                        shield_damage = turret_row.get('shield_damage', 0)
                        reload_time = turret_row.get('reload_time', 1.0)
                        range_val = turret_row.get('range', 0)
                        
                        # Calculate effective damage
                        effective_damage = max(damage or 0, hull_damage or 0, shield_damage or 0)
                        
                        # Calculate DPS
                        if reload_time > 0:
                            turret_dps = effective_damage / reload_time
                            total_dps += turret_dps
                        
                        # Track max range
                        if range_val > max_range:
                            max_range = range_val
        
        # If we don't have performance data, provide a basic rating based on count only
        if not has_performance_data:
            # Simple rating based on weapon/turret count and types
            total_count = weapon_count + turret_count
            if total_count >= 10:
                rating_score = 75
                rating_color = '#4CAF50'
                rating_text = 'Well Armed'
            elif total_count >= 5:
                rating_score = 60
                rating_color = '#FF9800'
                rating_text = 'Moderately Armed'
            elif total_count >= 2:
                rating_score = 40
                rating_color = '#FFC107'
                rating_text = 'Lightly Armed'
            else:
                rating_score = 20
                rating_color = '#F44336'
                rating_text = 'Minimal Armament'
        else:
            # Calculate combat rating (0-100 scale)
            # Base rating on total DPS with modifiers for range and count
            base_rating = min(total_dps / 50.0, 50)  # Up to 50 points for DPS
            range_bonus = min(max_range / 20000.0 * 25, 25)  # Up to 25 points for range
            count_bonus = min((weapon_count + turret_count) / 20.0 * 25, 25)  # Up to 25 points for weapon count
            
            rating_score = int(base_rating + range_bonus + count_bonus)
            
            # Determine rating color and text
            if rating_score >= 80:
                rating_color = '#4CAF50'  # Green
                rating_text = 'Excellent'
            elif rating_score >= 60:
                rating_color = '#FF9800'  # Orange
                rating_text = 'Good'
            elif rating_score >= 40:
                rating_color = '#FFC107'  # Yellow
                rating_text = 'Average'
            elif rating_score >= 20:
                rating_color = '#FF5722'  # Red-Orange
                rating_text = 'Poor'
            else:
                rating_color = '#F44336'  # Red
                rating_text = 'Very Poor'
        
        return {
            'total_dps': total_dps,
            'max_range': max_range,
            'weapon_count': weapon_count,
            'turret_count': turret_count,
            'rating_score': rating_score,
            'rating_color': rating_color,
            'rating_text': rating_text,
            'has_performance_data': has_performance_data
        }
    
    def estimate_travel_speed(self, travel_thrust, mass, engine_connections):
        """Estimate travel speed based on X4 physics approximations"""
        if not all(isinstance(x, (int, float)) and x > 0 for x in [travel_thrust, mass, engine_connections]):
            return 0.0
        
        # X4 physics approximation: travel speed = sqrt(total_travel_thrust / mass) * factor
        total_travel_thrust = travel_thrust * engine_connections
        speed_factor = 15.0  # Approximate X4 travel speed conversion factor
        return (total_travel_thrust / mass) ** 0.5 * speed_factor
    
    def estimate_max_speed(self, forward_thrust, mass, engine_connections):
        """Estimate maximum forward speed"""
        if not all(isinstance(x, (int, float)) and x > 0 for x in [forward_thrust, mass, engine_connections]):
            return 0.0
        
        # X4 physics approximation: max speed = sqrt(total_forward_thrust / mass) * factor
        total_forward_thrust = forward_thrust * engine_connections
        speed_factor = 12.0  # Forward speed is typically lower than travel
        return (total_forward_thrust / mass) ** 0.5 * speed_factor
    
    def estimate_boost_speed(self, boost_thrust, mass, engine_connections):
        """Estimate boost speed"""
        if not all(isinstance(x, (int, float)) and x > 0 for x in [boost_thrust, mass, engine_connections]):
            return 0.0
        
        # X4 physics approximation: boost speed = sqrt(total_boost_thrust / mass) * factor
        total_boost_thrust = boost_thrust * engine_connections
        speed_factor = 18.0  # Boost speed is typically highest
        return (total_boost_thrust / mass) ** 0.5 * speed_factor
    
    def calculate_engine_performance_rating(self, thrust_to_weight, travel_speed, max_speed):
        """Calculate overall engine performance rating"""
        # Base rating on thrust-to-weight ratio
        if thrust_to_weight >= 15:
            twr_score = 40
            twr_color = '#4CAF50'
        elif thrust_to_weight >= 10:
            twr_score = 30
            twr_color = '#FF9800'
        elif thrust_to_weight >= 5:
            twr_score = 20
            twr_color = '#FFC107'
        else:
            twr_score = 10
            twr_color = '#F44336'
        
        # Speed rating (combine travel and max speed)
        combined_speed = (travel_speed + max_speed) / 2
        if combined_speed >= 200:
            speed_score = 30
        elif combined_speed >= 150:
            speed_score = 25
        elif combined_speed >= 100:
            speed_score = 20
        elif combined_speed >= 50:
            speed_score = 15
        else:
            speed_score = 10
        
        # Overall rating (0-70 scale, converted to percentage)
        total_score = min(twr_score + speed_score, 70)
        percentage = int((total_score / 70) * 100)
        
        # Determine rating text and color
        if percentage >= 80:
            return f"<span style='color: #4CAF50;'>Excellent</span> ({percentage}%)"
        elif percentage >= 60:
            return f"<span style='color: #FF9800;'>Good</span> ({percentage}%)"
        elif percentage >= 40:
            return f"<span style='color: #FFC107;'>Average</span> ({percentage}%)"
        else:
            return f"<span style='color: #F44336;'>Poor</span> ({percentage}%)"
    
    def create_speed_performance_bars(self, travel_speed, max_speed, boost_speed):
        """Create visual speed performance bars with comparative metrics"""
        
        # Define speed benchmarks for scaling (typical X4 speeds)
        max_benchmark = 300  # Maximum expected speed for scaling
        
        # Calculate percentages
        travel_pct = min((travel_speed / max_benchmark) * 100, 100)
        max_pct = min((max_speed / max_benchmark) * 100, 100)
        boost_pct = min((boost_speed / max_benchmark) * 100, 100)
        
        # Color coding based on speed performance
        def get_speed_color(speed):
            if speed >= 200:
                return '#4CAF50'  # Green - Excellent
            elif speed >= 150:
                return '#8BC34A'  # Light Green - Very Good
            elif speed >= 100:
                return '#FFC107'  # Yellow - Good
            elif speed >= 50:
                return '#FF9800'  # Orange - Average
            else:
                return '#F44336'  # Red - Poor
        
        travel_color = get_speed_color(travel_speed)
        max_color = get_speed_color(max_speed)
        boost_color = get_speed_color(boost_speed)
        
        bars_html = f"""
        <div style='margin: 10px 0;'>
            <!-- Travel Speed Bar -->
            <div style='margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>
                    <span style='font-size: 11px; color: #BBB;'>Travel Speed</span>
                    <span style='font-size: 11px; color: {travel_color}; font-weight: bold;'>{travel_speed:.0f} m/s</span>
                </div>
                <div style='width: 100%; background: #444; height: 12px; border-radius: 6px; overflow: hidden;'>
                    <div style='width: {travel_pct:.1f}%; background: {travel_color}; height: 100%; border-radius: 6px; 
                                box-shadow: 0 0 6px rgba(255,255,255,0.4); transition: width 0.6s ease;'></div>
                </div>
            </div>
            
            <!-- Max Forward Speed Bar -->
            <div style='margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>
                    <span style='font-size: 11px; color: #BBB;'>Max Forward</span>
                    <span style='font-size: 11px; color: {max_color}; font-weight: bold;'>{max_speed:.0f} m/s</span>
                </div>
                <div style='width: 100%; background: #444; height: 12px; border-radius: 6px; overflow: hidden;'>
                    <div style='width: {max_pct:.1f}%; background: {max_color}; height: 100%; border-radius: 6px; 
                                box-shadow: 0 0 6px rgba(255,255,255,0.4); transition: width 0.6s ease;'></div>
                </div>
            </div>
            
            <!-- Boost Speed Bar -->
            <div style='margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>
                    <span style='font-size: 11px; color: #BBB;'>Boost Speed</span>
                    <span style='font-size: 11px; color: {boost_color}; font-weight: bold;'>{boost_speed:.0f} m/s</span>
                </div>
                <div style='width: 100%; background: #444; height: 12px; border-radius: 6px; overflow: hidden;'>
                    <div style='width: {boost_pct:.1f}%; background: {boost_color}; height: 100%; border-radius: 6px; 
                                box-shadow: 0 0 6px rgba(255,255,255,0.4); transition: width 0.6s ease;'></div>
                </div>
            </div>
            
            <!-- Performance Scale Reference -->
            <div style='font-size: 9px; color: #666; margin-top: 8px; text-align: center;'>
                Scale: 50 m/s (Poor) → 150 m/s (Good) → 300+ m/s (Excellent)
            </div>
        </div>
        """
        
        return bars_html
    
    def create_defensive_stats_bars(self, hull, shield_connections):
        """Create visual bars for defensive statistics"""
        
        # Handle hull value
        hull_value = 0
        if isinstance(hull, (int, float)):
            hull_value = hull
        elif isinstance(hull, str) and hull.replace('.', '').replace(',', '').isdigit():
            hull_value = float(hull.replace(',', ''))
        
        # Handle shield connections
        shield_value = 0
        if isinstance(shield_connections, (int, float)):
            shield_value = shield_connections
        
        # Define benchmarks for scaling
        max_hull_benchmark = 100000  # Typical high-end hull value
        max_shield_benchmark = 6  # Typical max shield hardpoints
        
        # Calculate percentages
        hull_pct = min((hull_value / max_hull_benchmark) * 100, 100) if hull_value > 0 else 0
        shield_pct = min((shield_value / max_shield_benchmark) * 100, 100) if shield_value > 0 else 0
        
        # Color coding for defensive stats
        def get_hull_color(hull_val):
            if hull_val >= 50000:
                return '#4CAF50'  # Green - Excellent
            elif hull_val >= 25000:
                return '#8BC34A'  # Light Green - Very Good
            elif hull_val >= 10000:
                return '#FFC107'  # Yellow - Good
            elif hull_val >= 5000:
                return '#FF9800'  # Orange - Average
            else:
                return '#F44336'  # Red - Poor
        
        def get_shield_color(shield_val):
            if shield_val >= 4:
                return '#4CAF50'  # Green - Excellent
            elif shield_val >= 3:
                return '#8BC34A'  # Light Green - Very Good
            elif shield_val >= 2:
                return '#FFC107'  # Yellow - Good
            elif shield_val >= 1:
                return '#FF9800'  # Orange - Basic
            else:
                return '#F44336'  # Red - None
        
        hull_color = get_hull_color(hull_value)
        shield_color = get_shield_color(shield_value)
        
        bars_html = f"""
        <div style='margin: 10px 0;'>
            <!-- Hull Integrity Bar -->
            <div style='margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>
                    <span style='font-size: 11px; color: #BBB;'>Hull Integrity</span>
                    <span style='font-size: 11px; color: {hull_color}; font-weight: bold;'>{hull_value:,.0f} HP</span>
                </div>
                <div style='width: 100%; background: #444; height: 14px; border-radius: 7px; overflow: hidden;'>
                    <div style='width: {hull_pct:.1f}%; background: {hull_color}; height: 100%; border-radius: 7px; 
                                box-shadow: 0 0 8px rgba(255,255,255,0.4); transition: width 0.6s ease;'></div>
                </div>
            </div>
            
            <!-- Shield Hardpoints Bar -->
            <div style='margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>
                    <span style='font-size: 11px; color: #BBB;'>Shield Capacity</span>
                    <span style='font-size: 11px; color: {shield_color}; font-weight: bold;'>{shield_value} Hardpoint{"s" if shield_value != 1 else ""}</span>
                </div>
                <div style='width: 100%; background: #444; height: 14px; border-radius: 7px; overflow: hidden;'>
                    <div style='width: {shield_pct:.1f}%; background: {shield_color}; height: 100%; border-radius: 7px; 
                                box-shadow: 0 0 8px rgba(255,255,255,0.4); transition: width 0.6s ease;'></div>
                </div>
            </div>
            
            <!-- Defensive Rating Scale -->
            <div style='font-size: 9px; color: #666; margin-top: 8px; text-align: center;'>
                Defensive Scale: Hull (5k-100k HP) • Shields (1-6 Hardpoints)
            </div>
        </div>
        """
        
        return bars_html
    
    def create_ship_info_bars(self, ship_row):
        """Create visual indicators for ship size and mass characteristics"""
        
        # Get ship size and mass
        ship_size = ship_row.get('size_class', 'Unknown').upper()
        mass = ship_row.get('mass', 0)
        
        # Handle mass value
        mass_value = 0
        if isinstance(mass, (int, float)):
            mass_value = mass
        elif isinstance(mass, str) and mass.replace('.', '').replace(',', '').isdigit():
            mass_value = float(mass.replace(',', ''))
        
        # Size class mapping for visualization
        size_mapping = {
            'S': {'name': 'Small', 'percentage': 20, 'color': '#4CAF50'},
            'M': {'name': 'Medium', 'percentage': 40, 'color': '#2196F3'},
            'L': {'name': 'Large', 'percentage': 70, 'color': '#FF9800'},
            'XL': {'name': 'Extra Large', 'percentage': 100, 'color': '#F44336'}
        }
        
        size_info = size_mapping.get(ship_size, {'name': 'Unknown', 'percentage': 10, 'color': '#666'})
        
        # Mass scale (typical X4 ship masses)
        max_mass_benchmark = 50000  # Heavy ships
        mass_pct = min((mass_value / max_mass_benchmark) * 100, 100) if mass_value > 0 else 0
        
        def get_mass_color(mass_val):
            if mass_val >= 30000:
                return '#F44336'  # Red - Very Heavy
            elif mass_val >= 15000:
                return '#FF9800'  # Orange - Heavy
            elif mass_val >= 5000:
                return '#FFC107'  # Yellow - Medium
            elif mass_val >= 1000:
                return '#8BC34A'  # Light Green - Light
            else:
                return '#4CAF50'  # Green - Very Light
        
        mass_color = get_mass_color(mass_value)
        
        bars_html = f"""
        <div style='margin: 10px 0;'>
            <!-- Ship Size Class Indicator -->
            <div style='margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>
                    <span style='font-size: 11px; color: #BBB;'>Size Class</span>
                    <span style='font-size: 11px; color: {size_info["color"]}; font-weight: bold;'>{ship_size} - {size_info["name"]}</span>
                </div>
                <div style='width: 100%; background: #444; height: 14px; border-radius: 7px; overflow: hidden; position: relative;'>
                    <!-- Size scale background -->
                    <div style='position: absolute; width: 100%; height: 100%; background: linear-gradient(90deg, #4CAF50 0%, #2196F3 33%, #FF9800 66%, #F44336 100%); opacity: 0.3;'></div>
                    <!-- Size indicator -->
                    <div style='width: {size_info["percentage"]}%; background: {size_info["color"]}; height: 100%; border-radius: 7px; 
                                box-shadow: 0 0 8px rgba(255,255,255,0.4); transition: width 0.6s ease;'></div>
                </div>
                <div style='display: flex; justify-content: space-between; margin-top: 2px; font-size: 8px; color: #666;'>
                    <span>Small</span>
                    <span>Medium</span>
                    <span>Large</span>
                    <span>XL</span>
                </div>
            </div>
            
            <!-- Mass Indicator -->
            <div style='margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 2px;'>
                    <span style='font-size: 11px; color: #BBB;'>Ship Mass</span>
                    <span style='font-size: 11px; color: {mass_color}; font-weight: bold;'>{mass_value:,.0f} kg</span>
                </div>
                <div style='width: 100%; background: #444; height: 14px; border-radius: 7px; overflow: hidden;'>
                    <div style='width: {mass_pct:.1f}%; background: {mass_color}; height: 100%; border-radius: 7px; 
                                box-shadow: 0 0 8px rgba(255,255,255,0.4); transition: width 0.6s ease;'></div>
                </div>
            </div>
        </div>
        """
        
        return bars_html

class LanguageSelectionDialog(QDialog):
    """Dialog for selecting X4 language preference."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Language Selection")
        self.setMinimumSize(400, 300)
        
        # Get current language info
        self.current_lang_id = language_detector.get_language_id()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Select Language for Ship Names")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Current language info
        current_info = get_current_language_info()
        current_label = QLabel(f"Current: {current_info['language_name']} "
                              f"({current_info['mapping_count']} text entries)")
        current_label.setStyleSheet("color: #666; margin-bottom: 15px;")
        layout.addWidget(current_label)
        
        # Auto-detection group
        auto_group = QGroupBox("Automatic Detection")
        auto_layout = QVBoxLayout()
        
        self.auto_radio = QRadioButton("Auto-detect from system/game settings")
        self.auto_radio.setChecked(language_detector._user_override is None)
        auto_layout.addWidget(self.auto_radio)
        
        # Show what auto-detection found
        auto_lang_id = language_detector.detect_system_language()
        auto_lang_name = language_detector.get_language_name(auto_lang_id)
        auto_info = QLabel(f"   → Would select: {auto_lang_name}")
        auto_info.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px;")
        auto_layout.addWidget(auto_info)
        
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)
        
        # Manual selection group
        manual_group = QGroupBox("Manual Selection")
        manual_layout = QVBoxLayout()
        
        self.manual_radio = QRadioButton("Choose language manually:")
        self.manual_radio.setChecked(language_detector._user_override is not None)
        manual_layout.addWidget(self.manual_radio)
        
        # Language dropdown
        self.language_combo = QComboBox()
        self.language_combo.setEnabled(self.manual_radio.isChecked())
        
        # Populate language options
        available_languages = language_detector.get_available_languages()
        for lang_id, lang_name in sorted(available_languages.items(), key=lambda x: x[1]):
            self.language_combo.addItem(f"{lang_name} (ID: {lang_id})", lang_id)
            
        # Select current language if manual override is active
        if language_detector._user_override is not None:
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == language_detector._user_override:
                    self.language_combo.setCurrentIndex(i)
                    break
        else:
            # Select detected language in dropdown
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == self.current_lang_id:
                    self.language_combo.setCurrentIndex(i)
                    break
        
        manual_layout.addWidget(self.language_combo)
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
        
        # Connect radio button changes
        self.auto_radio.toggled.connect(self.on_selection_changed)
        self.manual_radio.toggled.connect(self.on_selection_changed)
        
        # Info label
        info_label = QLabel("Note: Language files are extracted from your X4 installation. "
                           "If a language is not available, English will be used as fallback.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 15px;")
        layout.addWidget(info_label)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def on_selection_changed(self):
        """Handle radio button selection changes."""
        self.language_combo.setEnabled(self.manual_radio.isChecked())
        
    def accept(self):
        """Apply language selection and close dialog."""
        if self.auto_radio.isChecked():
            # Clear manual override
            language_detector.clear_user_override()
        else:
            # Set manual override
            selected_lang_id = self.language_combo.currentData()
            if selected_lang_id is not None:
                language_detector.set_user_override(selected_lang_id)
                
        super().accept()
