import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import shutil

# Hide main tkinter window
root = tk.Tk()
root.withdraw()

REPO_URL = "https://github.com/OfekSaar1234/Signify-RealTime-SignLanguage-Avatar"
APP_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'SignifyApp')
REPO_DIR = os.path.join(APP_DIR, 'Signify-RealTime-SignLanguage-Avatar')
VENV_DIR = os.path.join(APP_DIR, 'venv')

def show_error(title, message):
    messagebox.showerror(title, message)
    sys.exit(1)

def show_info(title, message):
    messagebox.showinfo(title, message)

def check_dependencies():
    # Check Git
    if not shutil.which("git"):
        show_error("Git Required", "Git is not installed or not in your system PATH.\n\nPlease download and install Git from https://git-scm.com/downloads\nMake sure to check the option to add Git to your PATH during installation.")
    
    # Check Python
    python_cmd = None
    for cmd in ["py", "python", "python3"]:
        success, out, err = run_cmd([cmd, "--version"])
        if success and ("Python" in out or "Python" in err):
            python_cmd = cmd
            break
            
    if not python_cmd:
        show_error("Python Required", "A working Python installation was not found in your system PATH.\n\nPlease download and install Python from https://www.python.org/downloads/\nMake sure to check 'Add Python to PATH' during installation.")
        
    return python_cmd

def run_cmd(cmd, cwd=None):
    try:
        # Hide console window on Windows
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, startupinfo=startupinfo)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def update_or_clone():
    if not os.path.exists(APP_DIR):
        os.makedirs(APP_DIR)
        
    if os.path.exists(REPO_DIR):
        if os.path.exists(os.path.join(REPO_DIR, '.git')):
            # Pull latest
            success, out, err = run_cmd(["git", "pull"], cwd=REPO_DIR)
            if not success:
                show_error("Update Failed", f"Failed to pull latest updates from the server.\n\nError: {err}")
            return
        else:
            # Corrupted directory, not a git repo. Remove it before cloning.
            try:
                shutil.rmtree(REPO_DIR)
            except Exception as e:
                show_error("Directory Error", f"Failed to clean up corrupted installation directory.\n\nError: {str(e)}")
                return
            
    # Clone
    success, out, err = run_cmd(["git", "clone", "-b", "feature/lg-tv-poc-and-chrome-extension", REPO_URL], cwd=APP_DIR)
    if not success:
        show_error("Download Failed", f"Failed to download the application code.\n\nError: {err}")

from tkinter import simpledialog

def check_env(splash=None):
    env_path = os.path.join(REPO_DIR, ".env")
    if not os.path.exists(env_path):
        if splash:
            splash.withdraw()
        api_key = simpledialog.askstring("API Key Required", "Welcome!\n\nPlease enter your Deepgram API Key to continue:\n(This is required to run the real-time AI)")
        if splash:
            splash.deiconify()
            splash.update()
            
        if api_key:
            with open(env_path, "w") as f:
                f.write(f"DEEPGRAM_API_KEY={api_key.strip()}\n")
        else:
            show_error("API Key Required", "You must provide a Deepgram API Key to use this application.")

def setup_venv_and_run(python_cmd):
    # Create venv if not exists
    if not os.path.exists(VENV_DIR):
        success, out, err = run_cmd([python_cmd, "-m", "venv", VENV_DIR])
        if not success:
            show_error("Virtual Environment Failed", f"Failed to create Python virtual environment.\n\nError: {err}")
            
    # Determine paths
    if sys.platform == "win32":
        venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")
        venv_pythonw = os.path.join(VENV_DIR, "Scripts", "pythonw.exe")
        venv_pip = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        venv_pythonw = venv_python
        venv_pip = os.path.join(VENV_DIR, "bin", "pip")
        
    # Install requirements
    req_path = os.path.join(REPO_DIR, "requirements.txt")
    if os.path.exists(req_path):
        success, out, err = run_cmd([venv_pip, "install", "-r", req_path])
        if not success:
            show_error("Installation Failed", f"Failed to install dependencies.\n\nError: {err}")
            
    ext_dir = os.path.join(REPO_DIR, "chrome-extension")
    if os.path.exists(ext_dir) and not os.path.exists(os.path.join(ext_dir, "node_modules")):
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        if shutil.which(npm_cmd) or shutil.which("npm"):
            npm_path = shutil.which(npm_cmd) or shutil.which("npm")
            run_cmd([npm_path, "install"], cwd=ext_dir)

    # Run dashboard
    dash_path = os.path.join(REPO_DIR, "run_dashboard.py")
    
    # We use Popen so the launcher can exit and let the dashboard run
    try:
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([venv_pythonw, dash_path], cwd=REPO_DIR, creationflags=creationflags)
    except Exception as e:
        show_error("Launch Failed", f"Failed to start the dashboard.\n\nError: {str(e)}")

if __name__ == "__main__":
    # Show splash screen
    splash = tk.Toplevel(root)
    splash.title("Signify")
    splash.geometry("400x120")
    
    # Center the splash screen
    splash.update_idletasks()
    width = splash.winfo_width()
    height = splash.winfo_height()
    x = (splash.winfo_screenwidth() // 2) - (width // 2)
    y = (splash.winfo_screenheight() // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")
    
    splash.overrideredirect(True) # Remove window borders
    
    # Add border and background to splash
    frame = tk.Frame(splash, bg="#1E1E1E", highlightbackground="#3b82f6", highlightcolor="#3b82f6", highlightthickness=2)
    frame.pack(fill="both", expand=True)
    
    tk.Label(frame, text="Signify", font=("Helvetica", 16, "bold"), bg="#1E1E1E", fg="#ffffff").pack(pady=(20, 5))
    tk.Label(frame, text="Updating & Installing dependencies...\nThis may take a minute or two on first launch.", font=("Helvetica", 10), bg="#1E1E1E", fg="#a1a1aa").pack()
    splash.update()

    try:
        py_cmd = check_dependencies()
        update_or_clone()
        check_env(splash)
        setup_venv_and_run(py_cmd)
    finally:
        splash.destroy()
        root.destroy()
