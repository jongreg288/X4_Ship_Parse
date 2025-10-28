from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QFormLayout, QTabWidget,
    QMainWindow, QMenuBar, QMessageBox, QDialog, QDialogButtonBox, QGroupBox, QRadioButton
)
from PyQt6.QtCore import QTimer
from .logic import compute_travel_speed
from .language_detector import language_detector
from .data_parser import refresh_text_mappings, get_current_language_info
import re
import matplotlib
matplotlib.use('QtAgg')  # Use Qt backend for matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Version information (network-free main application)
CURRENT_VERSION = "0.1.3"

class ShipStatsApp(QMainWindow):
    def __init__(self, ships_df, engines_df):
        super().__init__()
        self.ships_df = ships_df
        self.engines_df = engines_df
        # Debug info - GUI received ship data successfully
        self.init_ui()
        
        # Check for updates after a short delay (non-blocking)
        QTimer.singleShot(2000, self.check_for_updates_silent)

    def init_ui(self):
        self.setWindowTitle("X4 Ship Stats Analyzer")
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create 4 tabs
        self.fighters_tab = self.create_ship_tab("fight", "Fighters")
        self.container_tab = self.create_ship_tab("trade", "Container Ships")
        self.solid_tab = self.create_ship_tab("solid", "Solid Cargo Ships")
        self.liquid_tab = self.create_ship_tab("liquid", "Liquid Cargo Ships")
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.fighters_tab, "Fighters")
        self.tab_widget.addTab(self.container_tab, "Container")
        self.tab_widget.addTab(self.solid_tab, "Solid")
        self.tab_widget.addTab(self.liquid_tab, "Liquid")
        
        main_layout.addWidget(self.tab_widget)
        
        # Add DLC disclaimer at the bottom in deep red
        dlc_disclaimer = QLabel(
            "DLC Ships are not yet supported, look for them to be added in future patches.\nThank you."
        )
        dlc_disclaimer.setStyleSheet(
            "color: #8B0000; "  # Deep red color
            "font-weight: bold; "
            "font-size: 11pt; "
            "padding: 10px; "
            "text-align: center;"
        )
        dlc_disclaimer.setWordWrap(True)
        from PyQt6.QtCore import Qt
        dlc_disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(dlc_disclaimer)
        
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
        """Check for updates silently (no dialog if no updates)."""
        # Disabled in executable to avoid network dependencies
        # Use separate X4_Updater.exe for update checking
        pass
    
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
            f"<p><a href='https://github.com/jongreg288/X4_Ship_Parse/releases'>GitHub Releases</a></p>"
            f"<p>Download the latest X4_Ship_Parser.exe if a newer version is available.</p>"
        )
    
    def open_github_page(self):
        """Open the GitHub repository page in browser."""
        import webbrowser
        webbrowser.open("https://github.com/jongreg288/X4_Ship_Parse")
    
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
            "About X4 Ship Stats Analyzer",
            f"""<h3>X4 Ship Stats Analyzer</h3>
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
    
    def create_ship_tab(self, cargo_filter, tab_name):
        """Create a tab with ship selection and stats for a specific cargo type."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter ships based on purpose or cargo type
        if cargo_filter == "fight":
            # Filter for ships with purpose primary="fight"
            filtered_ships = self.ships_df[
                self.ships_df['purpose_primary'] == 'fight'
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
        ship_dropdown.setToolTip(f"Select a {cargo_filter} ship to analyze.\nShows clean ship names from the game")
        
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
        engine_dropdown.setToolTip("Select an engine to pair with the ship.\nShows ship engines only (missiles, mines, drones, spacesuits excluded)")
        
        # Create stats label
        stats_label = QLabel(f"Select a {cargo_filter} ship and engine to see stats.")
        stats_label.setToolTip("Ship statistics display.\nHover over values for detailed explanations.")
        
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
        ship_dropdown.currentIndexChanged.connect(lambda: self.update_tab_ship_tooltip(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_tab_stats(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_tab_engine_tooltip(tab_data))
        
        # Connect signals for chart updates
        ship_dropdown.currentIndexChanged.connect(lambda: self.update_comparison_chart(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_comparison_chart(tab_data))
        
        # Create form layout
        form = QFormLayout()
        form.addRow("Ship:", ship_dropdown)
        form.addRow("Engine:", engine_dropdown)
        
        # Create matplotlib chart for comparison
        chart_canvas = self.create_comparison_chart()
        
        layout.addLayout(form)
        layout.addWidget(stats_label)
        layout.addWidget(QLabel("<b>Cargo/Speed Comparison (Top 5 Ships)</b>"))
        layout.addWidget(chart_canvas)
        tab_widget.setLayout(layout)
        
        # Store chart canvas in tab_data for updates
        tab_data['chart_canvas'] = chart_canvas
        
        # Store tab data as attribute
        setattr(self, f'{cargo_filter}_tab_data', tab_data)
        
        return tab_widget

    def create_comparison_chart(self):
        """Create a matplotlib chart widget for ship comparison."""
        figure = Figure(figsize=(8, 4))
        canvas = FigureCanvas(figure)
        canvas.setMinimumHeight(300)
        return canvas
    
    def update_comparison_chart(self, tab_data):
        """Update the comparison chart with top 5 ships of same size using same engine."""
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
            ax.text(0.5, 0.5, 'Select a ship and engine to view comparison', 
                   ha='center', va='center', fontsize=12)
            ax.set_xticks([])
            ax.set_yticks([])
            chart_canvas.draw()
            return
        
        # Get the selected ship's size class
        ship_macro = ship_name_mapping.get(ship_name, ship_name)
        ship_size = self.extract_size_class(ship_macro)
        
        if not ship_size:
            ax = figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Unable to determine ship size', 
                   ha='center', va='center', fontsize=12)
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
                ratio = ((1000000 / storage_cargo_max) / (50000 / travel_speed))
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
            ax.text(0.5, 0.5, 'No comparable ships found', 
                   ha='center', va='center', fontsize=12)
            ax.set_xticks([])
            ax.set_yticks([])
            chart_canvas.draw()
            return
        
        # Create bar chart
        ax = figure.add_subplot(111)
        names = [s['name'][:30] + '...' if len(s['name']) > 30 else s['name'] for s in top_ships]
        ratios = [s['ratio'] for s in top_ships]
        colors = ['#4CAF50' if s['is_selected'] else '#2196F3' for s in top_ships]
        
        bars = ax.barh(names, ratios, color=colors)
        ax.set_xlabel('Time to Transport 1M Cargo over 50K Distance (Lower is Better)', fontsize=9)
        ax.set_title(f'Top 5 {ship_size.upper()}-Size Ships with {engine_name}', fontsize=11)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, ratio) in enumerate(zip(bars, ratios)):
            ax.text(ratio, bar.get_y() + bar.get_height()/2, 
                   f' {ratio:.2f}', va='center', fontsize=9)
        
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

        # Format storage information
        if storage_cargo_max > 0 and storage_cargo_type and storage_cargo_type != 'N/A':
            storage_display = f"{storage_cargo_max:,} ({storage_cargo_type})"
        else:
            storage_display = "None"

        # Calculate cargo-to-speed ratio
        cargo_speed_ratio = None
        if travel_speed is not None and travel_speed > 0 and storage_cargo_max > 0:
            cargo_speed_ratio = storage_cargo_max / travel_speed
            ratio_display = f"{cargo_speed_ratio:.2f}"
        else:
            ratio_display = "N/A"

        text = (
            f"<b>Ship:</b> {ship_display}<br>"
            f"<b>Hull Integrity:</b> {hull}<br>"
            f"<b>Storage:</b> {storage_display}<br>"
            f"<b>Engine:</b> {engine_display}<br>"
            f"<b>Travel Speed:</b> {travel_speed_display}<br>"
            f"<b>Cargo/Speed Ratio:</b> {ratio_display}"
        )
        stats_label.setText(text)
        stats_label.setWordWrap(True)  # Enable word wrap for better display
        
        # Update tooltip with detailed information
        self.update_tab_detailed_tooltip(tab_data, ship_row, engine_row, travel_speed, storage_cargo_max, cargo_speed_ratio)

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
                tooltip_parts.append(f"• Cargo/Speed Ratio: {cargo_speed_ratio:.2f}")
                tooltip_parts.append(f"  → Higher values = Better cargo efficiency")
                tooltip_parts.append(f"  → Lower values = Better speed performance")
        
        if not tooltip_parts:
            tooltip_parts.append("Select a ship and engine to see detailed information")
            
        stats_label.setToolTip("\n".join(tooltip_parts))
    
    def update_tab_ship_tooltip(self, tab_data):
        """Update ship dropdown tooltip based on current selection."""
        ship_dropdown = tab_data['ship_dropdown']
        ship_name_mapping = tab_data['ship_name_mapping']
        filtered_ships = tab_data['filtered_ships']
        cargo_filter = tab_data['cargo_filter']
        
        ship_name = ship_dropdown.currentText()
        
        if ship_name == "None":
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
        engine_name = engine_dropdown.currentText()
        
        if engine_name == "None":
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
                tooltip += f"• Higher travel thrust = faster travel speed"
                
                engine_dropdown.setToolTip(tooltip)


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
