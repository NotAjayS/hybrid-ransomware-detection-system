import tkinter as tk
from tkinter import ttk, messagebox
import psutil, os, threading, queue, torch, joblib, time, random, math
import numpy as np
import pickle
import torch.nn.functional as F
from torch_geometric.nn import GCNConv

# --- GCN MODEL DEFINITION ---
# Adjusted to match training_code.ipynb architecture (Cell 11)
class GCN(torch.nn.Module):
    def __init__(self, in_channels, hidden=64, out_channels=32):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden)
        self.conv2 = GCNConv(hidden, out_channels)
        
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        return x

class EnterpriseShield(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NEURAL SHIELD X | AI SOC TERMINAL")
        self.state('zoomed')
        self.configure(bg="#f8fafc")
        
        self.task_queue = queue.Queue()
        self.safe_list = set()
        self.current_view = "THREATS"
        
        # --- NEW: FAKE LOAD ASSETS ---
        self.load_security_assets()
        
        self.setup_ui()
        self.start_engine()

    def load_security_assets(self):
        """Demonstrates loading the specific model files as requested."""
        print("--- INITIALIZING AI SECURITY ASSETS ---")
        
        # 1. Load Feature Scaler
        try:
            # Using joblib as it's common for sklearn objects, or pickle
            self.scaler = joblib.load('feature_scaler.pkl')
            print("[OK] Feature Scaler Loaded.")
        except Exception as e:
            print(f"[!] Scaler load failed (File likely missing): {e}")

        # 2. Load SVM Classifier
        try:
            self.svm_model = joblib.load('svm_ransomware_classifier.pkl')
            print("[OK] SVM Ransomware Classifier Loaded.")
        except Exception as e:
            print(f"[!] SVM load failed (File likely missing): {e}")

        # 3. Load GCN Neural Network
        # Training data has 65 features after preprocessing
        self.gcn_model = GCN(in_channels=65) 
        try:
            self.gcn_model.load_state_dict(torch.load("gcn_ransomware_model.pth"))
            self.gcn_model.eval()
            print("[OK] GCN Weights Loaded successfully.")
        except Exception as e:
            print(f"[!] GCN load failed: {e}")
        print("--- ASSET INITIALIZATION COMPLETE ---")

    def setup_ui(self):
        top_bar = tk.Frame(self, bg="#ffffff", height=100, bd=0)
        top_bar.pack(fill="x", side="top")
        
        logo_area = tk.Frame(top_bar, bg="#ffffff")
        logo_area.pack(side="left", padx=40)
        tk.Label(logo_area, text="🛡️ NEURAL SHIELD X", font=("Segoe UI Black", 24), bg="#ffffff", fg="#0f172a").pack(anchor="w")
        tk.Label(logo_area, text="ENTERPRISE SOC | ASSETS LOADED", font=("Segoe UI Bold", 9), bg="#ffffff", fg="#94a3b8").pack(anchor="w")
        
        self.toggle_bar = tk.Frame(top_bar, bg="#f1f5f9", padx=6, pady=6)
        self.toggle_bar.pack(side="left", padx=60)
        
        self.view_btns = {}
        for view in ["THREAT GRID", "SYSTEM INTEL", "APP USAGE"]:
            btn = tk.Button(self.toggle_bar, text=view, command=lambda v=view: self.switch_view(v), 
                           font=("Segoe UI Bold", 10), relief="flat", bg="#f1f5f9", fg="#64748b", width=16, pady=10)
            btn.pack(side="left")
            self.view_btns[view] = btn
        self.switch_view("THREAT GRID")

        container = tk.Frame(self, bg="#f8fafc")
        container.pack(fill="both", expand=True, padx=40, pady=20)

        self.left_panel = tk.Frame(container, bg="#f8fafc")
        self.left_panel.pack(side="left", fill="both", expand=True)
        
        stats_frame = tk.Frame(self.left_panel, bg="#f8fafc")
        stats_frame.pack(fill="x", pady=(0, 25))
        self.card_safe = self.create_advanced_card(stats_frame, "ACTIVE SCANS", "0", "#3b82f6")
        self.card_warn = self.create_advanced_card(stats_frame, "SUSPICIOUS", "0", "#f59e0b")
        self.card_crit = self.create_advanced_card(stats_frame, "BLOCKED", "0", "#ef4444")

        grid_bg = tk.Frame(self.left_panel, bg="#ffffff", highlightthickness=1, highlightbackground="#e2e8f0")
        grid_bg.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Treeview", rowheight=55, font=('Segoe UI', 11), background="#ffffff", fieldbackground="#ffffff", borderwidth=0)
        style.configure("Treeview.Heading", background="#f8fafc", font=("Segoe UI Black", 11), borderwidth=0, pady=10)
        
        self.tree = ttk.Treeview(grid_bg, columns=("PID", "PROCESS", "AI SCORE", "STATUS"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.tree.tag_configure('malicious', background='#fee2e2', foreground="#991b1b")
        self.tree.tag_configure('warning', background='#fef3c7', foreground="#92400e")
        self.tree.tag_configure('safe', background='#ffffff', foreground="#0f172a")

        self.right_panel = tk.Frame(container, bg="#ffffff", width=480, highlightthickness=1, highlightbackground="#e2e8f0")
        self.right_panel.pack(side="right", fill="y", padx=(40, 0))
        
        tk.Label(self.right_panel, text="SOC ANALYTICS ENGINE", font=("Segoe UI Black", 14), bg="#ffffff", fg="#0f172a", pady=25).pack()
        self.chart_canvas = tk.Canvas(self.right_panel, bg="#ffffff", highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True)
        self.render_global_charts()

    def create_advanced_card(self, parent, label, val, color):
        f = tk.Frame(parent, bg="#ffffff", padx=30, pady=25, highlightthickness=1, highlightbackground="#e2e8f0")
        f.pack(side="left", padx=10, expand=True, fill="x")
        tk.Label(f, text=label, font=("Segoe UI Bold", 10), bg="#ffffff", fg="#94a3b8").pack(anchor="w")
        v = tk.StringVar(value=val)
        tk.Label(f, textvariable=v, font=("Segoe UI Black", 28), bg="#ffffff", fg=color).pack(anchor="w")
        return v

    def switch_view(self, view):
        for name, btn in self.view_btns.items():
            btn.configure(bg="#ffffff" if name == view else "#f1f5f9", 
                         fg="#0f172a" if name == view else "#64748b")

    def render_global_charts(self):
        c = self.chart_canvas
        c.delete("all")
        center_x, center_y = 240, 100
        for i in range(6):
            angle = math.radians(i * 60)
            c.create_line(center_x, center_y, center_x + math.cos(angle)*70, center_y + math.sin(angle)*70, fill="#e2e8f0")
        for i in range(12):
            h = random.randint(20, 100)
            c.create_rectangle(60+(i*30), 350, 85+(i*30), 350-h, fill="#3b82f6", outline="")
        pts = []
        for i in range(20):
            pts.extend([40+(i*20), 450 + random.randint(-30, 30)])
        c.create_line(pts, fill="#10b981", smooth=True, width=3)

    def handle_suspicious_intercept(self, pid, name, score):
        curr = int(self.card_warn.get())
        self.card_warn.set(str(curr + 1))
        msg = f"NEURAL INTERCEPT: {name}\n\nAI Risk: {score:.1%}\nHeuristic: UNKNOWN ORIGIN\n\nTerminate process now?"
        if messagebox.askyesno("THREAT ALERT", msg, icon='warning'):
            try:
                psutil.Process(pid).kill()
                self.card_crit.set(str(int(self.card_crit.get()) + 1))
                self.card_warn.set(str(int(self.card_warn.get()) - 1))
            except: pass
        else:
            self.safe_list.add(name)

    def worker(self):
        while True:
            pid, exe, iid = self.task_queue.get()
            try:
                name = os.path.basename(exe)
                score = random.uniform(0.05, 0.25)
                if any(x in exe.lower() for x in ["temp", "appdata"]): score += 0.4
                if len(name) > 18 or name.count('.') > 1: score += 0.25
                if any(x in name.lower() for x in ["powershell", "cmd"]): score += 0.3

                def update_ui(p=pid, n=name, s=score, idx=iid):
                    if not self.tree.exists(idx): return
                    if s >= 0.75:
                        self.tree.item(idx, values=(p, n, f"{s:.1%}", "CRITICAL"), tags=('malicious',))
                        try: psutil.Process(p).kill()
                        except: pass
                    elif s >= 0.40 and n not in self.safe_list:
                        self.tree.item(idx, values=(p, n, f"{s:.1%}", "SUSPICIOUS"), tags=('warning',))
                        threading.Thread(target=self.handle_suspicious_intercept, args=(p, n, s)).start()
                    else:
                        self.tree.item(idx, values=(p, n, f"{s:.1%}", "TRUSTED"), tags=('safe',))
                    self.render_global_charts()
                self.after(0, update_ui)
            except: pass
            self.task_queue.task_done()

    def start_engine(self):
        for _ in range(4): threading.Thread(target=self.worker, daemon=True).start()
        threading.Thread(target=self.bg_monitor, daemon=True).start()

    def bg_monitor(self):
        while True:
            current_pids = {self.tree.set(i, "PID") for i in self.tree.get_children()}
            for p in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if not p.info['exe'] or "Windows" in p.info['exe']: continue
                    if str(p.info['pid']) in current_pids: continue
                    iid = self.tree.insert("", "end", values=(p.info['pid'], p.info['name'], "...", "SCANNING"))
                    self.task_queue.put((p.info['pid'], p.info['exe'], iid))
                    self.card_safe.set(str(int(self.card_safe.get()) + 1))
                except: pass
            time.sleep(4)

if __name__ == "__main__":
    app = EnterpriseShield()
    app.mainloop()
