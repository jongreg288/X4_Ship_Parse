"""
Loading dialog for showing progress during data extraction
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import sys


class LoadingDialog(QDialog):
    """Simple loading dialog to show progress during data extraction."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("X4 ShipMatrix - Loading")
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        
        # Center the dialog on screen
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Title label
        title_label = QLabel("Loading X4 Ship Data...")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def update_status(self, message: str):
        """Update the status message."""
        self.status_label.setText(message)
        QApplication.processEvents()  # Ensure UI updates
    
    def set_progress(self, value: int, maximum: int = 100):
        """Set progress bar to determinate mode with specific value."""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
        QApplication.processEvents()
    
    def set_indeterminate(self):
        """Set progress bar to indeterminate mode."""
        self.progress_bar.setRange(0, 0)
        QApplication.processEvents()


# Global variable to hold the dialog instance
_loading_dialog = None


def show_loading_dialog():
    """Show a loading dialog for console-less execution."""
    global _loading_dialog
    
    # Only create if we don't have a console (windowed mode)
    # Check if stdout is None (executable mode) or not a tty (no console)
    if sys.stdout is None or not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        _loading_dialog = LoadingDialog()
        _loading_dialog.show()
        app.processEvents()
    
    return _loading_dialog


def update_loading_status(message: str):
    """Update loading dialog status if it exists."""
    global _loading_dialog
    if _loading_dialog:
        _loading_dialog.update_status(message)


def close_loading_dialog():
    """Close the loading dialog if it exists."""
    global _loading_dialog
    if _loading_dialog:
        _loading_dialog.close()
        _loading_dialog = None