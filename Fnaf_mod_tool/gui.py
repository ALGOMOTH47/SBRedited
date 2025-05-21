import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import os
import json

CONFIG_FILE = "config.json"

SCRIPTS = {
    "Generate Materials": "Scripts/AutoMaterialGenerator_V5.py",
    "Apply Materials": "Scripts/AutoMatiral3dModelConverterV2.py",
    "Reconstruct Map": "Scripts/SBMapReconstuctV4.py",}

class UE4PythonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unreal Engine 4.27 Python Tool Launcher")

        self.project_path = tk.StringVar()
        self.uecmd_path = tk.StringVar()

        self.load_config()

        # UE4 Cmd path
        tk.Label(root, text="Select UnrealEditor-Cmd.exe:").pack()
        tk.Entry(root, textvariable=self.uecmd_path, width=60).pack(pady=5)
        tk.Button(root, text="Browse UE4 Cmd", command=self.browse_uecmd).pack()

        # Project file path
        tk.Label(root, text="Select .uproject file:").pack()
        tk.Entry(root, textvariable=self.project_path, width=60).pack(pady=5)
        tk.Button(root, text="Browse Project", command=self.browse_project).pack()

        # Script checkboxes
        tk.Label(root, text="Select scripts to run:").pack(pady=(10, 0))
        self.script_vars = {}
        for name in SCRIPTS:
            var = tk.BooleanVar()
            self.script_vars[name] = var
            tk.Checkbutton(root, text=name, variable=var).pack(anchor="w")

        tk.Button(root, text="Run Selected Scripts", command=self.run_scripts).pack(pady=10)

        # Console output box
        tk.Label(root, text="Output:").pack()
        self.console = scrolledtext.ScrolledText(root, width=80, height=15)
        self.console.pack(padx=10, pady=(0, 10))

    def browse_project(self):
        file = filedialog.askopenfilename(filetypes=[("Unreal Project", "*.uproject")])
        if file:
            self.project_path.set(file)
            self.save_config()

    def browse_uecmd(self):
        file = filedialog.askopenfilename(filetypes=[("ue4", "UnrealEditor-Cmd.exe")])
        if file:
            self.uecmd_path.set(file)
            self.save_config()

    def run_scripts(self):
        self.console.delete(1.0, tk.END)  # Clear console

        project = self.project_path.get()
        uecmd = self.uecmd_path.get()

        if not uecmd or not os.path.exists(uecmd):
            messagebox.showerror("Error", "Please select a valid UnrealEditor-Cmd.exe path.")
            return
        if not project or not os.path.exists(project):
            messagebox.showerror("Error", "Please select a valid .uproject file.")
            return

        selected_scripts = [SCRIPTS[name] for name, var in self.script_vars.items() if var.get()]
        if not selected_scripts:
            messagebox.showinfo("Nothing Selected", "No scripts selected.")
            return

        for script in selected_scripts:
            script_full_path = os.path.abspath(script)
            cmd = [
                uecmd,
                project,
                f"-ExecutePythonScript={script_full_path}"
            ]
            cmd_str = " ".join(f'"{c}"' if ' ' in c else c for c in cmd)
            self.console.insert(tk.END, f"Running command:\n{cmd_str}\n\n")
            self.console.insert(tk.END, f"Resolved script path: {script_full_path}\n\n")
            self.console.see(tk.END)

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                self.console.insert(tk.END, result.stdout)
                self.console.insert(tk.END, result.stderr)
                if result.returncode != 0:
                    self.console.insert(tk.END, f"\n[ERROR] Script failed with code {result.returncode}\n")
                else:
                    self.console.insert(tk.END, f"\n[SUCCESS] Script finished.\n")
            except Exception as e:
                self.console.insert(tk.END, f"\n[EXCEPTION] {e}\n")

            self.console.insert(tk.END, "-"*80 + "\n")
            self.console.see(tk.END)

    def save_config(self):
        data = {
            "project_path": self.project_path.get(),
            "uecmd_path": self.uecmd_path.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.project_path.set(data.get("project_path", ""))
                    self.uecmd_path.set(data.get("uecmd_path", ""))
            except Exception as e:
                print("Failed to load config:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = UE4PythonGUI(root)
    root.mainloop()