## X4 ShipMatrix - Version-Aware Update System

### Overview
The X4 ShipMatrix now implements a sophisticated version-aware update system that distinguishes between different types of updates:

- **Major Updates (x.0.0)**: New features, breaking changes - always notified
- **Minor Updates (0.x.0)**: Feature additions, improvements - notify based on user preference
- **Patch Updates (0.0.x)**: Bug fixes, small improvements - notify based on user preference

### Update Behavior

#### Silent Update Checking
- The main application automatically checks for updates 2 seconds after startup
- Uses the separate `X4_Updater.exe` with `--silent` flag
- Only shows notifications based on user preferences

#### Manual Update Checking
- Available through **Help > Check for Updates...**
- Always shows current status and available updates
- Allows immediate download and installation

### Configuration
Update notification preferences are stored in `updater_config.ini`:

```ini
[updater]
# Notification level: 'all', 'major', 'none'
notification_level = major
last_notification_version = 0.0.0
last_check_date = 
auto_check_enabled = true
```

#### Notification Levels:
- **major**: Only notify for major version changes (default)
- **all**: Notify for all updates (major, minor, patch)
- **none**: Never show update notifications

### Technical Implementation

#### Version Comparison Logic
- Semantic versioning (x.y.z)
- Proper handling of version padding and comparison
- Type classification for appropriate user experience

#### Update Process
1. Silent background check on startup
2. Version-aware notification filtering
3. User preference tracking
4. Download and installation handling

### Benefits
- **Reduced notification fatigue**: Only important updates interrupt workflow
- **User control**: Configurable notification preferences
- **Seamless experience**: Silent checks don't impact performance
- **Complete coverage**: Manual checking always available

### Files Structure
```
X4 ShipMatrix.exe          # Main application (63.7 MB)
X4_Updater.exe            # Update utility (14.4 MB) - built from standalone_updater.py
updater_config.ini        # User preferences and configuration
README_USERS.txt          # User documentation
standalone_updater.py     # Source code for X4_Updater.exe (version-aware system)
```

### Clean Architecture
- **Main Application**: Uses external updater executable only
- **No Internal Dependencies**: No network calls or update logic in main app
- **Separation of Concerns**: Update functionality isolated in standalone utility
- **Single Source of Truth**: `standalone_updater.py` is the only update implementation

This implementation ensures users stay informed about important updates while maintaining an unobtrusive experience for routine maintenance updates.