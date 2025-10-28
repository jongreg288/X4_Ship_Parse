"""
Standalone X4 Ship Parser Update Checker
This can be built as a separate executable for update management.
"""

import requests
import json
import sys
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk

# Configuration
CURRENT_VERSION = "0.1.3"
GITHUB_REPO = "jongreg288/X4_Ship_Parse"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
MAIN_EXE_NAME = "X4_Ship_Parser.exe"

def compare_versions(current, latest):
    """Compare version strings."""
    try:
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        
        for c, l in zip(current_parts, latest_parts):
            if l > c:
                return True
            elif l < c:
                return False
        return False
    except:
        return False

def check_for_updates():
    """Check if a new version is available."""
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        
        release_data = response.json()
        latest_version = release_data['tag_name'].lstrip('v')
        
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
    except Exception as e:
        return {'error': str(e)}

def download_and_install_update(update_info):
    """Download and install the update."""
    assets = update_info.get('assets', [])
    exe_asset = None
    
    for asset in assets:
        if asset['name'].lower().endswith('.exe'):
            exe_asset = asset
            break
    
    if not exe_asset:
        webbrowser.open(update_info['download_url'])
        return False
    
    try:
        # Download to temp directory
        response = requests.get(exe_asset['browser_download_url'], stream=True)
        response.raise_for_status()
        
        temp_file = os.path.join(tempfile.gettempdir(), exe_asset['name'])
        
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Replace current executable
        current_exe = Path(MAIN_EXE_NAME)
        if current_exe.exists():
            backup_exe = current_exe.with_suffix('.exe.backup')
            current_exe.rename(backup_exe)
        
        # Move new executable
        Path(temp_file).rename(current_exe)
        
        messagebox.showinfo("Update Complete", 
                           f"X4 Ship Parser has been updated to version {update_info['latest_version']}!\n"
                           "The application will now launch.")
        
        # Launch updated application
        subprocess.Popen([str(current_exe)])
        return True
        
    except Exception as e:
        messagebox.showerror("Update Failed", f"Failed to install update: {e}")
        return False

def main():
    """Main updater function."""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Check for updates
    try:
        result = check_for_updates()
        
        if 'error' in result:
            messagebox.showerror("Update Check Failed", 
                               f"Could not check for updates:\n{result['error']}")
            return
        
        if not result['update_available']:
            response = messagebox.askyesno("No Updates", 
                                         f"You have the latest version ({result['current_version']}).\n"
                                         "Launch X4 Ship Parser now?")
            if response:
                subprocess.Popen([MAIN_EXE_NAME])
            return
        
        # Update available
        message = (f"Update Available!\n\n"
                  f"Current Version: {result['current_version']}\n"
                  f"Latest Version: {result['latest_version']}\n\n"
                  f"Would you like to download and install the update?")
        
        response = messagebox.askyesnocancel("Update Available", message)
        
        if response is True:  # Yes - download update
            if download_and_install_update(result):
                return  # Successfully updated and launched
        elif response is False:  # No - launch current version
            subprocess.Popen([MAIN_EXE_NAME])
        # Cancel - do nothing
        
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error: {e}")

if __name__ == "__main__":
    main()