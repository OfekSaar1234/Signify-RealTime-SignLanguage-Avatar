$venvPython = "C:\Users\User\Desktop\Signify\venv\Scripts\python.exe"
Write-Host "Installing PyInstaller..."
& $venvPython -m pip install pyinstaller
Write-Host "Building executable..."
& $venvPython -m PyInstaller --noconfirm --onefile --windowed --icon=icon.ico --name Signify launcher.py
Write-Host "Build complete. Executable is in the dist folder."
