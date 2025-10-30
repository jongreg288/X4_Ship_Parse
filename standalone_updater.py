"""
Standalone X4 ShipMatrix Update Checker
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
import configparser
from datetime import datetime, timedelta

# Configuration
CURRENT_VERSION = "0.2.1 alpha"
GITHUB_REPO = "jongreg288/X4_ShipMatrix"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
MAIN_EXE_NAME = "X4 ShipMatrix.exe"
CONFIG_FILE = "updater_config.ini"

def parse_version(version_string):
    """Parse version string into components."""
    try:
        return [int(x) for x in version_string.split('.')]
    except:
        return [0, 0, 0]

def compare_versions(current, latest):
    """Compare version strings and return update type."""
    try:
        current_parts = parse_version(current)
        latest_parts = parse_version(latest)
        
        # Pad shorter version with zeros
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        
        # Check if update is available
        is_newer = False
        for c, l in zip(current_parts, latest_parts):
            if l > c:
                is_newer = True
                break
            elif l < c:
                break
        
        if not is_newer:
            return {'update_available': False, 'update_type': 'none'}
        
        # Determine update type
        if len(current_parts) >= 1 and len(latest_parts) >= 1:
            if latest_parts[0] > current_parts[0]:  # Major version change (x.0.0)
                return {'update_available': True, 'update_type': 'major'}
            elif len(current_parts) >= 2 and len(latest_parts) >= 2:
                if latest_parts[1] > current_parts[1]:  # Minor version change (0.x.0)
                    return {'update_available': True, 'update_type': 'minor'}
                else:  # Patch version change (0.0.x)
                    return {'update_available': True, 'update_type': 'patch'}
        
        return {'update_available': True, 'update_type': 'patch'}
    except:
        return {'update_available': False, 'update_type': 'none'}

def load_config():
    """Load updater configuration."""
    config = configparser.ConfigParser()
    default_config = {
        'notification_level': 'major',  # 'all', 'major', 'none'
        'last_notification_version': '0.0.0',
        'last_check_date': '',
        'auto_check_enabled': 'true'
    }
    
    if Path(CONFIG_FILE).exists():
        config.read(CONFIG_FILE)
        if 'updater' not in config:
            config.add_section('updater')
        # Ensure all keys exist
        for key, value in default_config.items():
            if key not in config['updater']:
                config['updater'][key] = value
    else:
        config.add_section('updater')
        for key, value in default_config.items():
            config['updater'][key] = value
    
    return config

def save_config(config):
    """Save updater configuration."""
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)

def should_notify(update_type, config):
    """Determine if user should be notified based on preferences."""
    notification_level = config['updater'].get('notification_level', 'major')
    
    if notification_level == 'none':
        return False
    elif notification_level == 'major':
        return update_type == 'major'
    elif notification_level == 'all':
        return update_type in ['major', 'minor', 'patch']
    
    return False

def check_for_updates(silent_mode=False):
    """Check if a new version is available."""
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        
        release_data = response.json()
        latest_version = release_data['tag_name'].lstrip('v')
        
        update_info = compare_versions(CURRENT_VERSION, latest_version)
        
        if update_info['update_available']:
            result = {
                'update_available': True,
                'latest_version': latest_version,
                'current_version': CURRENT_VERSION,
                'update_type': update_info['update_type'],
                'release_notes': release_data.get('body', ''),
                'download_url': release_data.get('html_url', ''),
                'assets': release_data.get('assets', [])
            }
            
            # In silent mode, check if we should notify
            if silent_mode:
                config = load_config()
                if should_notify(update_info['update_type'], config):
                    last_notified = config['updater'].get('last_notification_version', '0.0.0')
                    # Only notify if we haven't already notified for this version
                    if compare_versions(last_notified, latest_version)['update_available']:
                        result['should_notify'] = True
                    else:
                        result['should_notify'] = False
                else:
                    result['should_notify'] = False
            
            return result
        else:
            return {
                'update_available': False,
                'latest_version': latest_version,
                'current_version': CURRENT_VERSION,
                'update_type': 'none'
            }
    except Exception as e:
        return {'error': str(e)}

def notify_update_available(current_version, latest_version, update_type):
    """Show update notification with appropriate message based on update type."""
    update_type_text = {
        'major': 'Major Update',
        'minor': 'Minor Update', 
        'patch': 'Patch Update'
    }.get(update_type, 'Update')
    
    message = (f"{update_type_text} Available!\n\n"
              f"Current Version: {current_version}\n"
              f"Latest Version: {latest_version}\n\n"
              f"Would you like to check for updates now?")
    
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()
    
    response = messagebox.askyesno(update_type_text, message)
    if response:
        # Launch the full updater
        import subprocess
        subprocess.Popen([sys.executable, __file__])
    
    root.destroy()

def silent_update_check():
    """Perform silent update check for background operations."""
    try:
        config = load_config()
        
        # Check if auto-check is enabled
        if config['updater'].get('auto_check_enabled', 'true').lower() != 'true':
            return
        
        result = check_for_updates(silent_mode=True)
        
        if 'error' in result:
            return  # Silent failure
        
        if result.get('update_available') and result.get('should_notify'):
            notify_update_available(
                result['current_version'], 
                result['latest_version'], 
                result['update_type']
            )
            
            # Update config with notification
            config['updater']['last_notification_version'] = result['latest_version']
            config['updater']['last_check_date'] = datetime.now().isoformat()
            save_config(config)
        else:
            # Update last check date only
            config['updater']['last_check_date'] = datetime.now().isoformat()
            save_config(config)
            
    except Exception:
        pass  # Silent failure

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
                           f"X4 ShipMatrix has been updated to version {update_info['latest_version']}!\n"
                           "The application will now launch.")
        
        # Launch updated application
        subprocess.Popen([str(current_exe)])
        return True
        
    except Exception as e:
        messagebox.showerror("Update Failed", f"Failed to install update: {e}")
        return False

def main():
    """Main updater function."""
    # Check if running in silent mode
    if len(sys.argv) > 1 and sys.argv[1] == '--silent':
        silent_update_check()
        return
    
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
                                         "Launch X4 ShipMatrix now?")
            if response:
                subprocess.Popen([MAIN_EXE_NAME])
            return
        
        # Update available
        update_type_text = {
            'major': 'Major Update',
            'minor': 'Minor Update', 
            'patch': 'Patch Update'
        }.get(result.get('update_type', 'unknown'), 'Update')
        
        message = (f"{update_type_text} Available!\n\n"
                  f"Current Version: {result['current_version']}\n"
                  f"Latest Version: {result['latest_version']}\n\n"
                  f"Would you like to download and install the update?")
        
        response = messagebox.askyesnocancel(update_type_text, message)
        
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