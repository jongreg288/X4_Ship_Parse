"""
Setup GUI for X4 Ship Parse application.
Provides a user-friendly interface for data extraction setup.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QTextEdit, 
    QProgressBar, QMessageBox, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from .x4_data_extractor import X4DataExtractor


class DataExtractionThread(QThread):
    """Thread for running data extraction without blocking the GUI."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, x4_path: Path):
        super().__init__()
        self.x4_path = x4_path
        
    def run(self):
        try:
            extractor = X4DataExtractor()
            extractor.x4_install_path = self.x4_path
            
            self.progress.emit("Starting data extraction...")
            success = extractor.extract_xml_files()
            
            if success:
                self.progress.emit("Validating extracted data...")
                success = extractor.validate_data_directory()
                
            self.finished.emit(success)
            
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.finished.emit(False)


class SetupDialog(QDialog):
    """GUI dialog for setting up X4 data extraction."""
    
    def __init__(self):
        super().__init__()
        self.extractor = X4DataExtractor()
        self.x4_path = None
        self.setup_ui()
        self.auto_detect_x4()
        
    def setup_ui(self):
        self.setWindowTitle("X4 Ship Parse - Data Setup")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("X4 Ship Parse - Data Setup")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "This application needs access to X4: Foundations game data files.\n"
            "We'll help you locate and extract the required XML files."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        # X4 Path Selection Group
        path_group = QGroupBox("X4 Installation Path")
        path_layout = QVBoxLayout()
        
        self.path_label = QLabel("X4 installation not found")
        path_layout.addWidget(self.path_label)
        
        path_buttons = QHBoxLayout()
        self.auto_detect_btn = QPushButton("Auto-Detect X4")
        self.browse_btn = QPushButton("Browse...")
        
        self.auto_detect_btn.clicked.connect(self.auto_detect_x4)
        self.browse_btn.clicked.connect(self.browse_x4_path)
        
        path_buttons.addWidget(self.auto_detect_btn)
        path_buttons.addWidget(self.browse_btn)
        path_layout.addLayout(path_buttons)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # Progress Group
        progress_group = QGroupBox("Extraction Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(150)
        self.progress_text.setReadOnly(True)
        progress_layout.addWidget(self.progress_text)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        self.extract_btn = QPushButton("Extract X4 Data")
        self.extract_btn.setEnabled(False)
        self.extract_btn.clicked.connect(self.start_extraction)
        
        self.skip_btn = QPushButton("Skip (Manual Setup)")
        self.skip_btn.clicked.connect(self.skip_setup)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.extract_btn)
        button_layout.addWidget(self.skip_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def auto_detect_x4(self):
        """Automatically detect X4 installation."""
        self.progress_text.append("🔍 Searching for X4: Foundations installation...")
        
        x4_path = self.extractor.find_x4_installation()
        
        if x4_path:
            self.x4_path = x4_path
            self.path_label.setText(f"Found: {x4_path}")
            self.path_label.setStyleSheet("color: green;")
            self.extract_btn.setEnabled(True)
            self.progress_text.append(f"✅ X4 found at: {x4_path}")
        else:
            self.path_label.setText("X4 installation not found")
            self.path_label.setStyleSheet("color: red;")
            self.extract_btn.setEnabled(False)
            self.progress_text.append("❌ X4 installation not found automatically")
            self.progress_text.append("Please use 'Browse...' to locate X4.exe manually")
            
    def browse_x4_path(self):
        """Browse for X4 installation directory."""
        file_dialog = QFileDialog()
        x4_exe = file_dialog.getOpenFileName(
            self,
            "Locate X4.exe",
            "",
            "X4 Executable (X4.exe);;All Files (*)"
        )[0]
        
        if x4_exe:
            x4_path = Path(x4_exe).parent
            if x4_path.exists() and (x4_path / "X4.exe").exists():
                self.x4_path = x4_path
                self.path_label.setText(f"Selected: {x4_path}")
                self.path_label.setStyleSheet("color: green;")
                self.extract_btn.setEnabled(True)
                self.progress_text.append(f"✅ X4 manually selected: {x4_path}")
            else:
                self.progress_text.append("❌ Invalid X4 installation directory")
                
    def start_extraction(self):
        """Start the data extraction process."""
        if not self.x4_path:
            return
            
        self.extract_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start extraction in background thread
        self.extraction_thread = DataExtractionThread(self.x4_path)
        self.extraction_thread.progress.connect(self.update_progress)
        self.extraction_thread.finished.connect(self.extraction_finished)
        self.extraction_thread.start()
        
    def update_progress(self, message: str):
        """Update progress display."""
        self.progress_text.append(message)
        
    def extraction_finished(self, success: bool):
        """Handle extraction completion."""
        self.progress_bar.setVisible(False)
        self.extract_btn.setEnabled(True)
        
        if success:
            self.progress_text.append("✅ Data extraction completed successfully!")
            QMessageBox.information(
                self,
                "Success",
                "X4 data has been extracted successfully!\nYou can now close this dialog and run the application."
            )
        else:
            self.progress_text.append("❌ Data extraction failed.")
            QMessageBox.warning(
                self,
                "Extraction Failed",
                "Could not extract X4 data automatically.\n"
                "Please refer to the manual setup instructions in README.md"
            )
            
    def skip_setup(self):
        """Skip automatic setup and proceed with manual instructions."""
        QMessageBox.information(
            self,
            "Manual Setup",
            "For manual setup instructions, please see README.md\n\n"
            "You'll need to:\n"
            "1. Extract X4 .cat/.dat files using modding tools\n"
            "2. Copy XML files to the 'data' directory\n"
            "3. Ensure proper directory structure"
        )
        self.close()


def show_setup_dialog():
    """Show the setup dialog."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    dialog = SetupDialog()
    dialog.exec()
    
    return app


if __name__ == "__main__":
    app = show_setup_dialog()
    sys.exit(app.exec())