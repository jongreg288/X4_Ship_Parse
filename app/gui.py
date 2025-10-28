from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QFormLayout, QTabWidget
)
from .logic import compute_travel_speed

class ShipStatsApp(QWidget):
    def __init__(self, ships_df, engines_df):
        super().__init__()
        self.ships_df = ships_df
        self.engines_df = engines_df
        print(f"GUI received {len(self.ships_df)} ships.")
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("X4 Ship Stats Analyzer")
        main_layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create 4 tabs
        self.all_ships_tab = self.create_ship_tab("all", "All Ships")
        self.container_tab = self.create_ship_tab("container", "Container Ships")
        self.solid_tab = self.create_ship_tab("solid", "Solid Cargo Ships")
        self.liquid_tab = self.create_ship_tab("liquid", "Liquid Cargo Ships")
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.all_ships_tab, "All Ships")
        self.tab_widget.addTab(self.container_tab, "Container")
        self.tab_widget.addTab(self.solid_tab, "Solid")
        self.tab_widget.addTab(self.liquid_tab, "Liquid")
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def create_ship_tab(self, cargo_filter, tab_name):
        """Create a tab with ship selection and stats for a specific cargo type."""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter ships based on cargo type
        if cargo_filter == "all":
            filtered_ships = self.ships_df
        elif cargo_filter == "container":
            filtered_ships = self.ships_df[
                self.ships_df['storage_cargo_type'].str.contains('container', na=False, case=False)
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
        
        # Create engine dropdown
        engine_dropdown = QComboBox()
        engine_names = ["None"] + self.engines_df["name"].tolist()
        engine_dropdown.addItems(engine_names)
        engine_dropdown.setToolTip("Select an engine to pair with the ship.\nHigher travel thrust = faster travel speed")
        
        # Create stats label
        stats_label = QLabel(f"Select a {cargo_filter} ship and engine to see stats.")
        stats_label.setToolTip("Ship statistics display.\nHover over values for detailed explanations.")
        
        # Store references for this tab
        tab_data = {
            'ship_dropdown': ship_dropdown,
            'engine_dropdown': engine_dropdown,
            'stats_label': stats_label,
            'ship_name_mapping': ship_name_mapping,
            'filtered_ships': filtered_ships,
            'cargo_filter': cargo_filter
        }
        
        # Connect signals
        ship_dropdown.currentIndexChanged.connect(lambda: self.update_tab_stats(tab_data))
        ship_dropdown.currentIndexChanged.connect(lambda: self.update_tab_ship_tooltip(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_tab_stats(tab_data))
        engine_dropdown.currentIndexChanged.connect(lambda: self.update_tab_engine_tooltip(tab_data))
        
        # Create form layout
        form = QFormLayout()
        form.addRow("Ship:", ship_dropdown)
        form.addRow("Engine:", engine_dropdown)
        
        layout.addLayout(form)
        layout.addWidget(stats_label)
        tab_widget.setLayout(layout)
        
        # Store tab data as attribute
        setattr(self, f'{cargo_filter}_tab_data', tab_data)
        
        return tab_widget

    def update_tab_stats(self, tab_data):
        ship_dropdown = tab_data['ship_dropdown']
        engine_dropdown = tab_data['engine_dropdown']
        stats_label = tab_data['stats_label']
        ship_name_mapping = tab_data['ship_name_mapping']
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
            matched_eng = self.engines_df[self.engines_df["name"] == engine_name]
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
        engine_display = engine_row.get('name', 'None') if engine_row is not None else 'None'

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
        engine_name = engine_dropdown.currentText()
        
        if engine_name == "None":
            engine_dropdown.setToolTip("Select an engine to pair with the ship.\nHigher travel thrust = faster travel speed")
        else:
            # Find the selected engine
            matched_eng = self.engines_df[self.engines_df["name"] == engine_name]
            if not matched_eng.empty:
                engine = matched_eng.iloc[0]
                travel_thrust = engine.get('travel_thrust', 'N/A')
                forward_thrust = engine.get('forward_thrust', 'N/A')
                boost_thrust = engine.get('boost_thrust', 'N/A')
                
                tooltip = f"ENGINE: {engine_name}\n"
                tooltip += f"• Travel Thrust: {travel_thrust}\n"
                tooltip += f"• Forward Thrust: {forward_thrust}\n"
                tooltip += f"• Boost Thrust: {boost_thrust}\n"
                tooltip += f"• Higher travel thrust = faster travel speed"
                
                engine_dropdown.setToolTip(tooltip)
