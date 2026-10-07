@echo off
setlocal
cd /d "%~dp0"
echo ========================================
echo   File Renamer 1.6.1 - Windows Builder
echo ========================================
echo.
py -m pip install --upgrade pyinstaller customtkinter
if errorlevel 1 goto :error
echo.
echo Building FileRenamer.exe ...
py -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "FileRenamer" ^
  --version-file "version_info.txt" ^
  --collect-all customtkinter ^
  "FileRenamer.py"
if errorlevel 1 goto :error
echo.
echo Build complete!
explorer "%~dp0dist"
pause
exit /b 0
:error
echo.
echo Build failed.
pause
exit /b 1
