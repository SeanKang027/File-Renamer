# File Renamer

A lightweight Windows batch file renaming utility built with Python and CustomTkinter.

## Features
- Live rename preview and natural filename sorting
- Sort by filename, creation time, modified time, or file size
- Ascending / descending order
- Filter all files, images only, or custom extensions
- Custom prefix, separator, starting number, and number padding
- Collision detection, safe two-stage rename, rollback, and one-level Undo
- Light / Dark mode and Windows High-DPI support
- Standalone Windows EXE build with PyInstaller

## Run from source
```bash
pip install -r requirements.txt
python FileRenamer.py
```

## Build Windows EXE
On Windows, double-click `build_windows.bat`. The finished executable is created at `dist\FileRenamer.exe`.

Undo history is stored in `%LOCALAPPDATA%\FileRenamer\rename_history.json`.

## Version
Current release: **1.6.1**

## License
MIT License.
