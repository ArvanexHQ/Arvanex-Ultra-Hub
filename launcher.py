import customtkinter as ctk
import webbrowser
import os
import threading
import string
import json
import re
import time
from PIL import Image
from icoextract import IconExtractor
from pypresence import Presence

class SmoothButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(font=("Segoe UI", 14, "bold"), hover=False)
        self.default_color = "#151515"
        self.configure(fg_color=self.default_color)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.configure(fg_color="#007AFF", font=("Segoe UI", 16, "bold"))
        
    def on_leave(self, event):
        self.configure(fg_color=self.default_color, font=("Segoe UI", 14, "bold"))

class ArvanexUltraLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Arvanex Ultra Hub V3")
        self.geometry("1250x850")
        self.configure(fg_color="#000000")

        self.db_file = "games_data.json"
        self.icon_dir = "cache_icons"
        if not os.path.exists(self.icon_dir): os.makedirs(self.icon_dir)
        
        self.all_game_cards = []
        self.found_games = {}
        
        # Discord RPC Setup
        self.rpc_id = "123456789012345678" 
        threading.Thread(target=self.init_discord_rpc, daemon=True).start()

        # Loading Frame
        self.loading_frame = ctk.CTkFrame(self, fg_color="#000000")
        self.loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.load_lbl = ctk.CTkLabel(self.loading_frame, text="ARVANEX", font=("Impact", 80), text_color="#007AFF")
        self.load_lbl.place(relx=0.5, rely=0.35, anchor="center")
        
        self.status_lbl = ctk.CTkLabel(self.loading_frame, text="READY TO SCAN", font=("Segoe UI", 16, "bold"), text_color="#FFFFFF")
        self.status_lbl.place(relx=0.5, rely=0.52, anchor="center")
        
        self.sub_status_lbl = ctk.CTkLabel(self.loading_frame, text="Waiting...", font=("Segoe UI", 12), text_color="#555555")
        self.sub_status_lbl.place(relx=0.5, rely=0.57, anchor="center")
        
        self.progress = ctk.CTkProgressBar(self.loading_frame, width=450, mode="determinate", progress_color="#007AFF")
        self.progress.place(relx=0.5, rely=0.63, anchor="center")
        self.progress.set(0)

        # Main UI
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.sidebar = ctk.CTkFrame(self.main_container, width=260, fg_color="#050505", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.logo = ctk.CTkLabel(self.sidebar, text="ARVANEX HQ", font=("Impact", 35), text_color="#007AFF")
        self.logo.pack(pady=40)

        self.user_lbl = ctk.CTkLabel(self.sidebar, text="USER: GUEST", font=("Segoe UI", 12, "bold"), text_color="#555555")
        self.user_lbl.pack(pady=10)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.filter_games)
        self.search_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Search Library...", textvariable=self.search_var, fg_color="#000000", border_color="#222222")
        self.search_entry.pack(pady=20, padx=20, fill="x")

        self.main_view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.main_view.pack(side="right", fill="both", expand=True, padx=40)

        self.header = ctk.CTkLabel(self.main_view, text="MY LIBRARY", font=("Segoe UI", 55, "bold"), text_color="#FFFFFF")
        self.header.pack(anchor="w", pady=(40, 5))

        self.scroll = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self.check_database()
        self.detect_active_user()

    def init_discord_rpc(self):
        try:
            self.RPC = Presence("1243160237767852033") 
            self.RPC.connect()
            self.RPC.update(details="Browsing Library", state="ARVANEX HQ Launcher", large_image="logo")
        except: pass

    def detect_active_user(self):
        steam_path = r"C:\Program Files (x86)\Steam\config\loginusers.vdf"
        if os.path.exists(steam_path):
            try:
                with open(steam_path, "r", encoding="utf-8") as f:
                    match = re.search(r'"PersonaName"\s+"(.*?)"', f.read())
                    if match: self.user_lbl.configure(text=f"USER: {match.group(1).upper()}")
            except: pass

    def check_database(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, "r") as f: self.found_games = json.load(f)
            for name, data in self.found_games.items(): self.add_game_card(name, data['icon'])
            self.show_main_ui()
        else: threading.Thread(target=self.fancy_launcher_scan, daemon=True).start()

    def fancy_launcher_scan(self):
        launchers = {
            "EPIC GAMES": ["Epic Games", "Program Files\\Epic Games"],
            "STEAM": ["SteamLibrary\\steamapps\\common", "Program Files (x86)\\Steam\\steamapps\\common"],
            "RIOT GAMES": ["Riot Games"],
            "XBOX & OTHERS": ["XboxGames", "Games", "Ubisoft\\Ubisoft Game Launcher\\games", "Origin Games"]
        }
        
        drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        total_steps = len(launchers)
        current_step = 0

        for l_name, l_paths in launchers.items():
            self.status_lbl.configure(text=f"SCANNING {l_name}...")
            for drive in drives:
                for sub in l_paths:
                    full_path = os.path.join(drive, sub)
                    if os.path.exists(full_path):
                        self.sub_status_lbl.configure(text=f"Checking: {full_path}")
                        try:
                            for folder in os.listdir(full_path):
                                game_path = os.path.join(full_path, folder)
                                if os.path.isdir(game_path):
                                    self.process_game(game_path, folder)
                        except: continue
            
            current_step += 1
            self.progress.set(current_step / total_steps)
            self.status_lbl.configure(text=f"{l_name} COMPLETED ✓", text_color="#00FF7F")
            time.sleep(0.5)
            self.status_lbl.configure(text_color="#FFFFFF")

        with open(self.db_file, "w") as f: json.dump(self.found_games, f)
        self.status_lbl.configure(text="ALL SYSTEMS READY", text_color="#007AFF")
        self.after(800, self.show_main_ui)

    def process_game(self, path, folder):
        name = folder.upper()
        if name in ["COMMON", "TEMP"]: return
        try:
            if any(f.lower().endswith(".exe") for f in os.listdir(path)):
                icon = self.extract_icon(path, name)
                self.found_games[name] = {"path": path, "icon": icon}
                self.after(0, lambda n=name, i=icon: self.add_game_card(n, i))
        except: pass

    def extract_icon(self, path, name):
        icon_path = os.path.join(self.icon_dir, f"{name}.png")
        if os.path.exists(icon_path): return icon_path
        try:
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.lower().endswith(".exe") and not any(x in f.lower() for x in ["crash", "report", "setup"]):
                        ext = IconExtractor(os.path.join(root, f))
                        ext.export_icon(icon_path)
                        return icon_path
                if root.count(os.sep) - path.count(os.sep) > 1: break
        except: pass
        return None

    def show_main_ui(self):
        self.loading_frame.place_forget()
        self.main_container.place(relx=0, rely=0, relwidth=1, relheight=1)

    def add_game_card(self, name, icon_path):
        card = ctk.CTkFrame(self.scroll, fg_color="#080808", corner_radius=20, border_width=1, border_color="#121212")
        card.pack(fill="x", pady=8, padx=5)

        img = None
        if icon_path and os.path.exists(icon_path):
            try:
                pil_img = Image.open(icon_path)
                img = ctk.CTkImage(pil_img, size=(45, 45))
            except: pass

        icon_box = ctk.CTkLabel(card, text="" if img else name[0], image=img, width=60, height=60, fg_color="#151515", corner_radius=12)
        icon_box.pack(side="left", padx=20, pady=15)

        lbl = ctk.CTkLabel(card, text=name, font=("Segoe UI", 18, "bold"), text_color="#FFFFFF")
        lbl.pack(side="left", padx=10)

        btn = SmoothButton(card, text="LAUNCH", width=140, height=45, corner_radius=12,
                           command=lambda n=name: self.launch_game(n))
        btn.pack(side="right", padx=25)
        self.all_game_cards.append({"frame": card, "name": name})

    def filter_games(self, *args):
        q = self.search_var.get().upper()
        for item in self.all_game_cards:
            item["frame"].pack(fill="x", pady=8) if q in item["name"] else item["frame"].pack_forget()

    def launch_game(self, name):
        try:
            # Update Discord Status
            if hasattr(self, 'RPC'):
                self.RPC.update(details=f"Playing {name}", state="via Arvanex Ultra Hub", start=time.time())
            
            uris = {"FORTNITE": "com.epicgames.launcher://apps/fn%3Afortnite?action=launch", "VALORANT": "riotclient://launch-app/bdragon", "CS": "steam://run/730"}
            for k, v in uris.items():
                if k in name: webbrowser.open(v); return
            
            path = self.found_games[name]["path"]
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.lower().endswith(".exe") and not any(x in f.lower() for x in ["crash", "report", "setup"]):
                        os.startfile(os.path.join(root, f))
                        return
        except: pass

if __name__ == "__main__":
    app = ArvanexUltraLauncher()
    app.mainloop()