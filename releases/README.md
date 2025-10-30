# Release Management

This directory manages release artifacts and version tracking for the X4 ShipMatrix.

## Structure

- `latest/` - Contains the most recent release files for distribution
- Future subdirectories may include version-specific releases

## Usage

The `latest/` folder is used by:
- Build scripts for organizing distribution files
- Release automation for GitHub releases
- Version management systems

## Files Not in Git

Large binary files (executables) are not tracked in git but may be present locally:
- `X4_Ship_Parser.exe` 
- `X4_Updater.exe`
- Distribution packages and archives

These files are managed through the build system and GitHub releases.