"""
Update checker for X4 Ship Parser
Checks for updates from GitHub releases and offers to download them.
"""

import requests
import json
import sys
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QProgressDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import webbrowser

# Current version - update this when releasing new versions
CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "jongreg288/X4_Ship_Parse"  # Update this to your actual GitHub repo
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class UpdateDownloader(QThread):
    """Thread for downloading updates in the background."""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, download_url, filename):
        super().__init__()
        self.download_url = download_url
        self.filename = filename
    
    def run(self):
        try:
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, self.filename)
            
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(progress)
            
            self.finished.emit(True, file_path)
            
        except Exception as e:
            self.finished.emit(False, str(e))

def compare_versions(current, latest):
    """Compare version strings (e.g., '0.0.0.1' vs '0.0.0.2')."""
    try:
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        
        for c, l in zip(current_parts, latest_parts):
            if l > c:
                return True  # Update available
            elif l < c:
                return False  # Current is newer
        
        return False  # Same version
    except:
        return False

def check_for_updates():
    """Check if a new version is available on GitHub."""
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        
        release_data = response.json()
        latest_version = release_data['tag_name'].lstrip('v')  # Remove 'v' prefix if present
        
        if compare_versions(CURRENT_VERSION, latest_version):
            return {
                'update_available': True,
                'latest_version': latest_version,
                'current_version': CURRENT_VERSION,
                'release_notes': release_data.get('body', ''),
                'download_url': release_data.get('html_url', ''),
                'assets': release_data.get('assets', [])
            }
        else:
            return {
                'update_available': False,
                'latest_version': latest_version,
                'current_version': CURRENT_VERSION
            }
            
    except requests.exceptions.RequestException:
        # Network error or API unavailable
        return None
    except Exception:
        # Other errors (JSON parsing, etc.)
        return None

def find_executable_asset(assets):
    """Find the Windows executable in the release assets."""
    for asset in assets:
        name = asset['name'].lower()
        if name.endswith('.exe') or name.endswith('.zip'):
            return asset
    return None

def show_update_dialog(parent, update_info):
    """Show update dialog with user confirmation."""
    latest_version = update_info['latest_version']
    current_version = update_info['current_version']
    release_notes = update_info['release_notes']
    
    # Create message box
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle("Update Available")
    msg_box.setIcon(QMessageBox.Icon.Information)
    
    # Main message
    message = f"""
<h3>New Version Available!</h3>
<p><b>Current Version:</b> {current_version}</p>
<p><b>Latest Version:</b> {latest_version}</p>
"""
    
    # Add release notes if available
    if release_notes:
        # Truncate release notes if too long
        notes = release_notes[:500] + "..." if len(release_notes) > 500 else release_notes
        message += f"""
<p><b>Release Notes:</b></p>
<p style="font-family: monospace; font-size: 9pt; background-color: #f0f0f0; padding: 8px;">
{notes.replace('\n', '<br>')}
</p>
"""
    
    message += "<p>Would you like to download the update?</p>"
    
    msg_box.setText(message)
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | 
        QMessageBox.StandardButton.No | 
        QMessageBox.StandardButton.Ignore
    )
    
    # Customize button text
    yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
    if yes_button:
        yes_button.setText("Download Update")
    
    no_button = msg_box.button(QMessageBox.StandardButton.No)
    if no_button:
        no_button.setText("Not Now")
    
    ignore_button = msg_box.button(QMessageBox.StandardButton.Ignore)
    if ignore_button:
        ignore_button.setText("Skip This Version")
    
    return msg_box.exec()

def download_update(parent, update_info):
    """Download and install the update."""
    assets = update_info.get('assets', [])
    executable_asset = find_executable_asset(assets)
    
    if not executable_asset:
        # No executable found, open browser to releases page
        QMessageBox.information(
            parent,
            "Manual Download Required",
            f"No executable file found in the release assets.\n"
            f"Please visit the GitHub releases page to download manually.\n\n"
            f"Opening browser..."
        )
        webbrowser.open(update_info['download_url'])
        return
    
    # Show progress dialog
    progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100, parent)
    progress_dialog.setWindowTitle("Downloading Update")
    progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
    progress_dialog.show()
    
    # Start download
    downloader = UpdateDownloader(
        executable_asset['browser_download_url'],
        executable_asset['name']  
    )
    
    def on_progress(value):
        progress_dialog.setValue(value)
    
    def on_finished(success, result):
        progress_dialog.close()
        
        if success:
            # Download successful
            file_path = result
            
            msg = QMessageBox(parent)
            msg.setWindowTitle("Download Complete")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(f"Update downloaded successfully!\n\nFile saved to: {file_path}")
            msg.setInformativeText("Would you like to open the download location?")
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                # Open file location
                if sys.platform == "win32":
                    subprocess.run(f'explorer /select,"{file_path}"', shell=True)
                else:
                    subprocess.run(["xdg-open", os.path.dirname(file_path)])
        else:
            # Download failed
            QMessageBox.critical(
                parent,
                "Download Failed",
                f"Failed to download update:\n{result}\n\n"
                f"Please try downloading manually from:\n{update_info['download_url']}"
            )
    
    downloader.progress.connect(on_progress)
    downloader.finished.connect(on_finished)
    downloader.start()
    
    # Handle cancel
    def on_cancel():
        downloader.terminate()
        progress_dialog.close()
    
    progress_dialog.canceled.connect(on_cancel)

def check_for_updates_with_ui(parent=None, silent=False):
    """
    Check for updates and show UI if update is available.
    
    Args:
        parent: Parent widget for dialogs
        silent: If True, don't show "no updates" message
    """
    update_info = check_for_updates()
    
    if update_info is None:
        # Network error or API unavailable
        if not silent:
            QMessageBox.warning(
                parent,
                "Update Check Failed",
                "Unable to check for updates.\n"
                "Please check your internet connection and try again."
            )
        return
    
    if not update_info['update_available']:
        # No update available
        if not silent:
            QMessageBox.information(
                parent,
                "No Updates Available",
                f"You are running the latest version ({update_info['current_version']})."
            )
        return
    
    # Update available - show dialog
    result = show_update_dialog(parent, update_info)
    
    if result == QMessageBox.StandardButton.Yes:
        # User wants to download
        download_update(parent, update_info)
    elif result == QMessageBox.StandardButton.Ignore:
        # User wants to skip this version
        # You could store this preference in settings if needed
        pass
    # No action needed for "Not Now"