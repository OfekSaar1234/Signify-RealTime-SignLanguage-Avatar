import os
import sys
import json
import subprocess
import threading
import ctypes
import customtkinter as ctk
from PIL import Image
import webbrowser

# Fix taskbar icon on Windows
try:
    myappid = 'signify.dashboard.gui.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Set appearance mode and color theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "app_settings.json")
LOGO_PATH = os.path.join(BASE_DIR, "gui", "assets", "logo.png")

# Human readable mappings
INPUT_MAP = {
    "Text Typing": "typing",
    "System Audio (Loopback)": "audio_loopback",
    "Microphone & System Audio": "dual_audio",
    "Web/Extension Audio": "websocket_audio"
}
INPUT_MAP_REV = {v: k for k, v in INPUT_MAP.items()}

OUTPUT_MAP = {
    "Local Display Window": "opencv",
    "OBS Virtual Camera": "virtual_cam"
}
OUTPUT_MAP_REV = {v: k for k, v in OUTPUT_MAP.items()}

class SignifyDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Signify - Control Dashboard")
        self.geometry("750x760")
        self.resizable(True, True) # Allow window resizing
        
        self.config_data = self.load_config()
        self.pipeline_process = None
        self.chrome_ext_process = None
        self.website_process = None

        self.setup_icon()
        self.setup_background()
        self.setup_ui()

    def setup_icon(self):
        """Convert PNG logo to ICO and set it as the window/taskbar icon."""
        if os.path.exists(LOGO_PATH):
            try:
                icon_path = os.path.join(BASE_DIR, "gui", "assets", "logo.ico")
                if not os.path.exists(icon_path):
                    img = Image.open(LOGO_PATH)
                    img.save(icon_path, format="ICO")
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"Could not load window icon: {e}")

    def setup_background(self):
        """Set a faded logo as a watermark background"""
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH).convert("RGBA")
                # Make it very transparent (e.g. 8% opacity) so text is highly readable
                alpha = img.split()[3]
                alpha = alpha.point(lambda p: p * 0.08)
                img.putalpha(alpha)
                
                bg_image = ctk.CTkImage(img, size=(600, 600))
                self.bg_label = ctk.CTkLabel(self, image=bg_image, text="")
                self.bg_label.place(relx=0.5, rely=0.5, anchor="center")
            except Exception as e:
                print(f"Could not load background watermark: {e}")

    def load_config(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "input_mode": "typing",
                "output_mode": "opencv",
                "network": {"enable_websocket": False},
                "playback": {"speed_ms": 33, "transition_frames": 5, "interpolation_frames": 4},
                "launch": {"core": True, "chrome_ext": False, "website": False}
            }

    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config_data, f, indent=2)

    def setup_ui(self):
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ---- HEADER (Logo & Title) ----
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, pady=(20, 10))

        if os.path.exists(LOGO_PATH):
            logo_img = ctk.CTkImage(light_image=Image.open(LOGO_PATH),
                                    dark_image=Image.open(LOGO_PATH),
                                    size=(60, 60))
            self.logo_label = ctk.CTkLabel(self.header_frame, image=logo_img, text="")
            self.logo_label.pack(side="left", padx=10)

        self.title_label = ctk.CTkLabel(
            self.header_frame, text="SIGNIFY SETTINGS", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.title_label.pack(side="left", padx=10)

        # ---- LEFT PANEL (Input/Output Settings) ----
        # Using semi-transparent color for frames to let watermark slightly show through
        frame_color = ("#e0e0e0", "#2b2b2b") 
        self.left_frame = ctk.CTkFrame(self, fg_color=frame_color)
        self.left_frame.grid(row=1, column=0, padx=(30, 15), pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.left_frame, text="Input & Output", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        # Input Mode
        ctk.CTkLabel(self.left_frame, text="Input Source:").pack(anchor="w", padx=20, pady=(10, 0))
        current_in = self.config_data.get("input_mode", "typing")
        self.input_mode_var = ctk.StringVar(value=INPUT_MAP_REV.get(current_in, "Text Typing"))
        self.input_dropdown = ctk.CTkOptionMenu(
            self.left_frame, 
            values=list(INPUT_MAP.keys()),
            variable=self.input_mode_var,
            command=self.update_config
        )
        self.input_dropdown.pack(fill="x", padx=20, pady=5)

        # Output Mode
        ctk.CTkLabel(self.left_frame, text="Output Display:").pack(anchor="w", padx=20, pady=(15, 0))
        current_out = self.config_data.get("output_mode", "opencv")
        self.output_mode_var = ctk.StringVar(value=OUTPUT_MAP_REV.get(current_out, "Local Display Window"))
        self.output_dropdown = ctk.CTkOptionMenu(
            self.left_frame, 
            values=list(OUTPUT_MAP.keys()),
            variable=self.output_mode_var,
            command=self.update_config
        )
        self.output_dropdown.pack(fill="x", padx=20, pady=5)

        # Advanced Checkboxes
        self.ws_var = ctk.BooleanVar(value=self.config_data.get("network", {}).get("enable_websocket", False))
        self.ws_switch = ctk.CTkSwitch(
            self.left_frame, 
            text="Enable WebSockets API", 
            variable=self.ws_var,
            command=self.update_config
        )
        self.ws_switch.pack(anchor="w", padx=20, pady=(25, 5))

        # ---- RIGHT PANEL (Playback Settings) ----
        self.right_frame = ctk.CTkFrame(self, fg_color=frame_color)
        self.right_frame.grid(row=1, column=1, padx=(15, 30), pady=10, sticky="nsew")

        ctk.CTkLabel(self.right_frame, text="Avatar Playback", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        playback_cfg = self.config_data.get("playback", {})

        # Speed MS
        self.speed_val_label = ctk.CTkLabel(self.right_frame, text=f"Speed (Delay ms): {playback_cfg.get('speed_ms', 33)}")
        self.speed_val_label.pack(anchor="w", padx=20, pady=(10, 0))
        self.speed_var = ctk.IntVar(value=playback_cfg.get("speed_ms", 33))
        self.speed_slider = ctk.CTkSlider(self.right_frame, from_=10, to=100, variable=self.speed_var, command=self.update_speed_label)
        self.speed_slider.pack(fill="x", padx=20, pady=5)

        # Transition Frames
        self.trans_val_label = ctk.CTkLabel(self.right_frame, text=f"Transition Frames: {playback_cfg.get('transition_frames', 5)}")
        self.trans_val_label.pack(anchor="w", padx=20, pady=(10, 0))
        self.trans_var = ctk.IntVar(value=playback_cfg.get("transition_frames", 5))
        self.trans_slider = ctk.CTkSlider(self.right_frame, from_=0, to=20, number_of_steps=20, variable=self.trans_var, command=self.update_trans_label)
        self.trans_slider.pack(fill="x", padx=20, pady=5)

        # Interpolation Frames
        self.interp_val_label = ctk.CTkLabel(self.right_frame, text=f"Interpolation Smoothing: {playback_cfg.get('interpolation_frames', 4)}")
        self.interp_val_label.pack(anchor="w", padx=20, pady=(10, 0))
        self.interp_var = ctk.IntVar(value=playback_cfg.get("interpolation_frames", 4))
        self.interp_slider = ctk.CTkSlider(self.right_frame, from_=0, to=10, number_of_steps=10, variable=self.interp_var, command=self.update_interp_label)
        self.interp_slider.pack(fill="x", padx=20, pady=5)

        # Avatar Scale Slider
        self.scale_val_label = ctk.CTkLabel(self.right_frame, text=f"Display Scale: {self.config_data.get('display', {}).get('scale', 0.35):.2f}")
        self.scale_val_label.pack(anchor="w", padx=20, pady=(10, 0))
        self.scale_var = ctk.DoubleVar(value=self.config_data.get("display", {}).get("scale", 0.35))
        self.scale_slider = ctk.CTkSlider(self.right_frame, from_=0.1, to=1.0, variable=self.scale_var, command=self.update_scale_label)
        self.scale_slider.pack(fill="x", padx=20, pady=5)

        # ---- LAUNCH SETTINGS ----
        self.launch_frame = ctk.CTkFrame(self, fg_color=frame_color)
        self.launch_frame.grid(row=2, column=0, columnspan=2, padx=30, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.launch_frame, text="Launch Settings", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, pady=(10, 5))
        
        self.launch_core_var = ctk.BooleanVar(value=self.config_data.get("launch", {}).get("core", True))
        self.launch_chrome_var = ctk.BooleanVar(value=self.config_data.get("launch", {}).get("chrome_ext", False))
        self.launch_website_var = ctk.BooleanVar(value=self.config_data.get("launch", {}).get("website", False))

        # Core
        ctk.CTkSwitch(self.launch_frame, text="Signify Core (main.py)", variable=self.launch_core_var, command=self.update_config).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.core_status_label = ctk.CTkLabel(self.launch_frame, text="Stopped", text_color="gray")
        self.core_status_label.grid(row=1, column=1, padx=20, pady=5, sticky="w")
        
        # Chrome Ext
        ctk.CTkSwitch(self.launch_frame, text="Chrome Extension", variable=self.launch_chrome_var, command=self.update_config).grid(row=2, column=0, padx=20, pady=5, sticky="w")
        self.chrome_status_label = ctk.CTkLabel(self.launch_frame, text="Stopped", text_color="gray")
        self.chrome_status_label.grid(row=2, column=1, padx=20, pady=5, sticky="w")

        # LG TV App
        ctk.CTkSwitch(self.launch_frame, text="LG TV App Server", variable=self.launch_website_var, command=self.update_config).grid(row=3, column=0, padx=20, pady=(5, 15), sticky="w")
        self.website_status_label = ctk.CTkLabel(self.launch_frame, text="Stopped", text_color="gray")
        self.website_status_label.grid(row=3, column=1, padx=20, pady=(5, 15), sticky="w")
        self.website_url_btn = ctk.CTkButton(self.launch_frame, text="Open UI", width=60, height=24, command=lambda: webbrowser.open("http://localhost:8080"), state="disabled")
        self.website_url_btn.grid(row=3, column=2, padx=10, pady=(5, 15), sticky="w")

        self.launch_frame.grid_columnconfigure(0, weight=1)
        self.launch_frame.grid_columnconfigure(1, weight=1)
        self.launch_frame.grid_columnconfigure(2, weight=1)

        # ---- BOTTOM PANEL (Launch Control) ----
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=3, column=0, columnspan=2, pady=(15, 5))

        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Status: Ready", text_color="gray")
        self.status_label.pack(pady=(0, 5))

        self.button_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.button_frame.pack()

        self.start_button = ctk.CTkButton(
            self.button_frame, 
            text="START SELECTED", 
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            width=200,
            fg_color="#10B981", # Emerald Green
            hover_color="#059669",
            command=self.toggle_signify
        )
        self.start_button.pack(side="left", padx=10)

        self.clear_button = ctk.CTkButton(
            self.button_frame, 
            text="CLEAR QUEUE (Ctrl+Space)", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            width=200,
            fg_color="#F59E0B", # Amber
            hover_color="#D97706",
            command=self.clear_queue,
            state="disabled"
        )
        self.clear_button.pack(side="right", padx=10)

        # ---- LIVE TYPING PANEL ----
        self.typing_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.typing_frame.grid(row=4, column=0, columnspan=2, pady=(5, 5), padx=30, sticky="ew")

        self.typing_entry = ctk.CTkEntry(
            self.typing_frame, 
            placeholder_text="Type an English sentence here and press Enter...", 
            height=40,
            state="disabled"
        )
        self.typing_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.typing_entry.bind("<Return>", self.send_text)

        self.send_button = ctk.CTkButton(
            self.typing_frame, text="Send", width=80, height=40, 
            command=self.send_text, state="disabled"
        )
        self.send_button.pack(side="right")

        # ---- LIVE FEEDBACK / TRANSLATION PANEL ----
        self.feedback_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.feedback_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10), padx=30, sticky="ew")

        self.translation_label = ctk.CTkLabel(
            self.feedback_frame, 
            text="Waiting for translation...", 
            font=ctk.CTkFont(size=15, slant="italic"), 
            text_color="gray"
        )
        self.translation_label.pack(pady=(5, 0))

        self.warning_label = ctk.CTkLabel(
            self.feedback_frame, 
            text="", 
            font=ctk.CTkFont(size=13), 
            text_color="#EF4444" # Red
        )
        self.warning_label.pack()

        # ---- CHROME EXTENSION SIDELOAD PANEL ----
        self.ext_frame = ctk.CTkFrame(self, fg_color=frame_color)
        self.ext_frame.grid(row=6, column=0, columnspan=2, pady=(0, 10), padx=30, sticky="ew")

        ctk.CTkLabel(self.ext_frame, text="Chrome Extension (Developer Mode Install)", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        instructions = (
            "1. Click the button below to save the .zip file to your Desktop.\n"
            "2. Extract the .zip file into a folder.\n"
            "3. Open Chrome and navigate to chrome://extensions\n"
            "4. Turn on 'Developer mode' in the top right corner.\n"
            "5. Click 'Load unpacked' and select the extracted folder."
        )
        ctk.CTkLabel(self.ext_frame, text=instructions, justify="left", font=ctk.CTkFont(size=12)).pack(padx=20, pady=5)
        
        self.ext_btn_frame = ctk.CTkFrame(self.ext_frame, fg_color="transparent")
        self.ext_btn_frame.pack(pady=10)
        
        self.copy_zip_btn = ctk.CTkButton(self.ext_btn_frame, text="Save .zip to Desktop", command=self.export_extension_zip)
        self.copy_zip_btn.pack(side="left", padx=10)
        
        self.ext_status_label = ctk.CTkLabel(self.ext_btn_frame, text="", font=ctk.CTkFont(size=12))
        self.ext_status_label.pack(side="left", padx=10)

    # Dynamic label updates
    def update_speed_label(self, val):
        self.speed_val_label.configure(text=f"Speed (Delay ms): {int(val)}")
        self.update_config()
        
    def update_trans_label(self, val):
        self.trans_val_label.configure(text=f"Transition Frames: {int(val)}")
        self.update_config()
        
    def update_interp_label(self, val):
        self.interp_val_label.configure(text=f"Interpolation Smoothing: {int(val)}")
        self.update_config()

    def update_scale_label(self, val):
        self.scale_val_label.configure(text=f"Display Scale: {val:.2f}")
        self.update_config()

    def update_config(self, *args):
        # Update config dictionary from UI variables
        self.config_data["input_mode"] = INPUT_MAP.get(self.input_mode_var.get(), "typing")
        self.config_data["output_mode"] = OUTPUT_MAP.get(self.output_mode_var.get(), "opencv")
        
        if "network" not in self.config_data:
            self.config_data["network"] = {}
        self.config_data["network"]["enable_websocket"] = self.ws_var.get()
        
        if "display" not in self.config_data:
            self.config_data["display"] = {}
        self.config_data["display"]["scale"] = float(f"{self.scale_var.get():.2f}")

        if "playback" not in self.config_data:
            self.config_data["playback"] = {}
        self.config_data["playback"]["speed_ms"] = int(self.speed_var.get())
        self.config_data["playback"]["transition_frames"] = int(self.trans_var.get())
        self.config_data["playback"]["interpolation_frames"] = int(self.interp_var.get())

        if "launch" not in self.config_data:
            self.config_data["launch"] = {}
        self.config_data["launch"]["core"] = self.launch_core_var.get()
        self.config_data["launch"]["chrome_ext"] = self.launch_chrome_var.get()
        self.config_data["launch"]["website"] = self.launch_website_var.get()

        # Save to disk
        self.save_config()

    def toggle_signify(self):
        # Check if any process is running
        any_running = False
        if self.pipeline_process and self.pipeline_process.poll() is None: any_running = True
        if self.chrome_ext_process and self.chrome_ext_process.poll() is None: any_running = True
        if self.website_process and self.website_process.poll() is None: any_running = True

        if not any_running:
            # Clear previous text
            self.translation_label.configure(text="Waiting for translation...", text_color="gray")
            self.warning_label.configure(text="")

            # Start Core
            if self.launch_core_var.get():
                main_script = os.path.join(BASE_DIR, "main.py")
                self.pipeline_process = subprocess.Popen(
                    [sys.executable, main_script], 
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1, # Line buffered
                    universal_newlines=True
                )
                threading.Thread(target=self.output_listener, daemon=True).start()
                self.core_status_label.configure(text="Running", text_color="#10B981")
            
            # Start Chrome Extension
            if self.launch_chrome_var.get():
                ext_dir = os.path.join(BASE_DIR, "chrome-extension")
                self.chrome_ext_process = subprocess.Popen(
                    "npm run dev", 
                    cwd=ext_dir,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                threading.Thread(target=self.node_output_listener, args=(self.chrome_ext_process, "Chrome Ext"), daemon=True).start()
                self.chrome_status_label.configure(text="Running", text_color="#10B981")

            # Start LG TV App Server
            if self.launch_website_var.get():
                web_dir = os.path.join(BASE_DIR, "website", "lg_tv_app")
                self.website_process = subprocess.Popen(
                    [sys.executable, "-m", "http.server", "8080"], 
                    cwd=web_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                threading.Thread(target=self.node_output_listener, args=(self.website_process, "LG TV App"), daemon=True).start()
                self.website_status_label.configure(text="Running", text_color="#10B981")
                self.website_url_btn.configure(state="normal")
            
            self.start_button.configure(text="STOP SELECTED", fg_color="#EF4444", hover_color="#DC2626") # Red
            self.status_label.configure(text="Status: Running", text_color="#10B981")

            # Enable typing if mode is typing and core is running
            if self.config_data.get("input_mode") == "typing" and self.launch_core_var.get():
                self.typing_entry.configure(state="normal")
                self.send_button.configure(state="normal")
            
            # Enable clear button
            self.clear_button.configure(state="normal")
        else:
            # Stop Processes
            if self.pipeline_process:
                self.pipeline_process.terminate()
                self.pipeline_process = None
                self.core_status_label.configure(text="Stopped", text_color="gray")
            
            if self.chrome_ext_process:
                subprocess.run(f"taskkill /F /T /PID {self.chrome_ext_process.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.chrome_ext_process = None
                self.chrome_status_label.configure(text="Stopped", text_color="gray")

            if self.website_process:
                self.website_process.terminate()
                self.website_process = None
                self.website_status_label.configure(text="Stopped", text_color="gray")
                self.website_url_btn.configure(state="disabled")
            
            self.start_button.configure(text="START SELECTED", fg_color="#10B981", hover_color="#059669")
            self.status_label.configure(text="Status: Stopped", text_color="gray")

            # Disable typing and clear
            self.typing_entry.configure(state="disabled")
            self.send_button.configure(state="disabled")
            self.clear_button.configure(state="disabled")

    def clear_queue(self):
        if self.pipeline_process and self.pipeline_process.poll() is None:
            try:
                self.pipeline_process.stdin.write("!CLEAR_QUEUE!\n")
                self.pipeline_process.stdin.flush()
            except Exception as e:
                print(f"Failed to send CLEAR command: {e}")

    def output_listener(self):
        """Reads stdout from the subprocess in the background to update the GUI."""
        if not self.pipeline_process:
            return

        try:
            for line in iter(self.pipeline_process.stdout.readline, ''):
                line = line.strip()
                if not line:
                    continue
                
                # Check for successful translations
                if "Translated to ASL:" in line:
                    try:
                        translation = line.split("Translated to ASL:")[1].strip()
                        # Update GUI safely from thread
                        self.after(0, lambda t=translation: self.translation_label.configure(text=f"ASL: {t}", text_color="#10B981"))
                        self.after(0, lambda: self.warning_label.configure(text="")) # clear warning
                    except Exception:
                        pass
                
                # Check for missing animations
                elif "Missing animation file for:" in line:
                    try:
                        word = line.split("Missing animation file for:")[1].split(".")[0].strip()
                        self.after(0, lambda w=word: self.warning_label.configure(text=f"⚠️ Missing animation for: '{w}'"))
                    except Exception:
                        pass
                        
                # Optional: print everything to terminal so we still see logs
                print(line)
                
        except Exception as e:
            print(f"Subprocess output listener closed: {e}")

    def node_output_listener(self, process, name):
        """Reads stdout from node processes and prints to terminal."""
        if not process: return
        try:
            for line in iter(process.stdout.readline, ''):
                line = line.strip()
                if line: print(f"[{name}] {line}")
        except Exception as e:
            print(f"[{name}] Listener closed: {e}")

    def send_text(self, event=None):
        if self.pipeline_process and self.pipeline_process.poll() is None:
            text = self.typing_entry.get()
            if text.strip():
                try:
                    self.pipeline_process.stdin.write(text + "\n")
                    self.pipeline_process.stdin.flush()
                    self.typing_entry.delete(0, 'end')
                except Exception as e:
                    print(f"Failed to send text: {e}")

    def export_extension_zip(self):
        import shutil
        src_zip = os.path.join(BASE_DIR, "chrome-extension", "signify-extension.zip")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop", "signify-extension.zip")
        try:
            if not os.path.exists(src_zip):
                self.ext_status_label.configure(text="Error: ZIP not found. Please build extension first.", text_color="#EF4444")
                return
            shutil.copy2(src_zip, desktop)
            self.ext_status_label.configure(text="Saved to Desktop!", text_color="#10B981")
        except Exception as e:
            self.ext_status_label.configure(text=f"Error: {e}", text_color="#EF4444")

if __name__ == "__main__":
    app = SignifyDashboard()
    app.mainloop()
