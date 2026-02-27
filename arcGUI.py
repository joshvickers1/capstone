# Import necessary modules
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import opendssdirect as dss 
import os, shutil
from pathlib import Path

# --- Input handling and OpenDSS integration ---

# --- SYSTEM MODEL INPUT HANDLING ---
# Function to import system model and provide ingestion summary 
def compile_and_summarize(master_path):
    # Store master path
    app.system_master_path = master_path
    # Compile modeln using OpenDSS
    dss.Text.Command(f'Compile "{str(master_path)}"')

    # Raise error if OpenDSS flags something
    if dss.Error.Number() != 0:
        err = dss.Error.Description()
        raise RuntimeError(f"OpenDSS compile error: {err}")

    # Summary with parsed info from compiled model
    summary = {
        "master_file": str(master_path),
        "circuit_name": dss.Circuit.Name().upper(),
        "num_buses": dss.Circuit.NumBuses(),
        "num_nodes": dss.Circuit.NumNodes(),
        "num_loads": dss.Loads.Count(),
        "num_transformers": dss.Transformers.Count(),
        "num_lines": dss.Lines.Count(),
        "num_capacitors": dss.Capacitors.Count(),
        "num_generators": dss.Generators.Count(),
        "converged": bool(dss.Solution.Converged()),
        }
    return summary

# Read dss files as strings
def read_dss_text(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="replace")

# --- DER INPUT HANDLING ---
# Get DER Settings as string
def set_der_from_file(app, der_file_path: str) -> None:
    app.der_text = read_dss_text(der_file_path)

# Get DER Setting 
def summarize_der_dss_text(dss_text: str) -> dict:
    element_counts = {}
    buses = set()
    total_kw = 0.0
    total_kvar = 0.0
    kv_values = []
    amps_values = []
    phases_values = []

    for raw in dss_text.splitlines():
        line = raw.strip()

        if not line or line.startswith("!"):
            continue

        lower = line.lower()

        # Count "New" elements
        if lower.startswith("new "):
            parts = line.split()
            if len(parts) >= 2:
                if "." in parts[1]:
                    cls = parts[1].split(".")[0].lower()
                    element_counts[cls] = element_counts.get(cls, 0) + 1

        # Get each part of the command lines to see what was added
        tokens = line.split()
        for token in tokens:
            if "=" not in token:
                continue

            key, value = token.split("=", 1)
            key = key.lower()

            if key == "bus1":
                buses.add(value)

            elif key == "kw":
                try:
                    total_kw += float(value)
                except:
                    pass

            elif key == "kvar":
                try:
                    total_kvar += float(value)
                except:
                    pass

            elif key == "kv":
                try:
                    kv_values.append(float(value))
                except:
                    pass

            elif key == "amps":
                try:
                    amps_values.append(float(value))
                except:
                    pass

            elif key == "phases":
                try:
                    phases_values.append(int(value))
                except:
                    pass

    return {
        "num_new_elements": sum(element_counts.values()),
        "element_counts": element_counts,
        "buses": sorted(buses),
        "total_kw": total_kw,
        "total_kvar": total_kvar,
        "kv_values": sorted(set(kv_values)),
        "amps_values": sorted(set(amps_values)),
        "phases_values": sorted(set(phases_values)),
    }

# Convert summary to string to send to GUI
def der_summary_to_string(path: str, summary: dict) -> str:
    lines = []
    lines.append("DER File Summary:\n")
    lines.append(f"File path: {path}")
    lines.append(f"New elements: {summary['num_new_elements']}")

    lines.append("By type:")
    for cls, count in summary["element_counts"].items():
        lines.append(f"  - {cls}: {count}")

    if summary["kv_values"]:
        lines.append(f"Total kW: {summary['total_kw']}")
    
    if summary["total_kvar"]:
        lines.append(f"Total kvar: {summary['total_kvar']}")

    if summary["kv_values"]:
        lines.append(f"kV values: {summary['kv_values']}")

    if summary["amps_values"]:
        lines.append(f"Amps values: {summary['amps_values']}")

    if summary["phases_values"]:
        lines.append(f"Phases: {summary['phases_values']}")

    lines.append(f"Buses referenced ({len(summary['buses'])}):")
    for b in summary["buses"]:
        lines.append(f"  - {b}")

    return "\n".join(lines)

def set_fault_from_file(app, fault_file_path: str) -> None:
    app.fault_text = read_dss_text(fault_file_path)

# Split building and running instructions in the system model file
_RUN_PREFIXES = ("solve", "export", "show", "plot", "visualize", "calcv", "clear", "reset")
def split_build_and_run(dss_text: str):
    build_lines, run_lines = [], []

    for raw in dss_text.splitlines():
        s = raw.strip()

        if not s or s.startswith("!"):
            build_lines.append(raw)
            continue

        # Remove trailing inline comment for matching
        s0 = s.split("!", 1)[0].strip().lower()

        if any(s0.startswith(p) for p in _RUN_PREFIXES):
            run_lines.append(raw)
        else:
            build_lines.append(raw)

    build_text = "\n".join(build_lines).strip() + "\n"
    run_text = "\n".join(run_lines).strip() + "\n"
    return build_text, run_text

# --- FAULT SCENARIO INPUT HANDLING ---
def set_fault_from_file(app, fault_file_path: str) -> None:
    app.fault_text = read_dss_text(fault_file_path)

# Create summary of Fault Scenario input
def summarize_fault_dss_text(dss_text: str) -> dict:
    faults = []

    for raw in dss_text.splitlines():
        line = raw.strip()

        if not line or line.startswith("!"):
            continue

        lower = line.lower()

        # Only look at Fault definitions
        if lower.startswith("new ") and "fault." in lower:
            tokens = line.split()

            fault_name = ""
            bus = None
            phases = None

            # Extract fault name (Fault.X)
            if len(tokens) >= 2 and "." in tokens[1]:
                fault_name = tokens[1]

            # Extract key=value pairs
            for token in tokens:
                if "=" not in token:
                    continue

                key, value = token.split("=", 1)
                key = key.lower()

                if key == "bus1":
                    bus = value

                elif key == "phases":
                    try:
                        phases = int(value)
                    except:
                        pass

            # Determine fault type from phases
            if phases == 3:
                fault_type = "3-Phase"
            elif phases == 2:
                fault_type = "Line-to-Line"
            elif phases == 1:
                fault_type = "Single Line-to-Ground"
            else:
                fault_type = "Unknown"

            faults.append({
                "name": fault_name,
                "bus": bus,
                "phases": phases,
                "type": fault_type
            })

    return {
        "num_faults": len(faults),
        "faults": faults
    }

# Convert fault summary to string to send to GUI
def fault_summary_to_string(path: str, summary: dict) -> str:
    lines = []
    lines.append("Fault Scenario Summary:\n")
    lines.append(f"File path: {path}")
    lines.append(f"Number of faults: {summary['num_faults']}")
    lines.append("")
    for f in summary["faults"]:
        lines.append(f"Fault: {f['name']}")
        lines.append(f"  Bus: {f['bus']}")
        lines.append(f"  Type: {f['type']}")
        lines.append("")
    return "\n".join(lines)

# Create final dss file to be compiled and ran for simulation
def combine_build_der_fault_run(system_build: str, der_text: str, fault_text: str, run_text: str) -> str:
    return (
        "Clear\n"
        "\n! ===== SYSTEM BUILD =====\n"
        + system_build
        + "\n! ===== DER =====\n"
        + (der_text.strip() + "\n" if der_text else "! (none)\n")
        + "\n! ===== FAULT SCENARIO =====\n"
        + (fault_text.strip() + "\n" if fault_text else "! (none)\n")
        #+ "\n! ===== RUN =====\n"
        #+ (run_text.strip() + "\n" if run_text else "Set mode=snap\nSolve\n")
    )

# Function to create the final dss file with all inputs considered
def write_final_dss_to_master_folder(system_master_path: str, final_dss_text: str,
                                    filename: str = "_GUI_Final_RunCase.dss") -> str:
    master = Path(system_master_path).expanduser().resolve()
    out_path = master.parent / filename
    out_path.write_text(final_dss_text, encoding="utf-8")
    return str(out_path)
        
# Function to run the simulation with all inputs considered
def run_simulation():
    # Update final dss text by combining all inputs
    app.final_dss_text = combine_build_der_fault_run(app.build_text, app.der_text, app.fault_text, "")
    # Check for runtime errors
    if not app.system_master_path:
        raise RuntimeError("No system model loaded.")
    if not app.final_dss_text:
        raise RuntimeError("Final DSS text is empty. Build it before running.")

    # Write final DSS into same folder as master for redirects
    final_path = write_final_dss_to_master_folder(app.system_master_path, app.final_dss_text)
    app.final_path = final_path
    # Make sure OpenDSS resolves relative Redirects from that folder
    final_file = Path(final_path).resolve()
    model_dir = final_file.parent

    dss.Basic.ClearAll()
    try:
        dss.Basic.DataPath(str(model_dir))
    except Exception:
        pass
    os.chdir(model_dir)

    # Now compile the FILE (not the text)
    dss.Text.Command(f'Compile "{str(final_file)}"')
    if dss.Error.Number() != 0:
        raise RuntimeError(f"OpenDSS compile error: {dss.Error.Description()}")

    # If your final DSS does NOT include Solve, do it here:
    # dss.Solution.Solve()

    if dss.Error.Number() != 0:
        raise RuntimeError(f"OpenDSS run error: {dss.Error.Description()}")

    # Optional: store where you wrote it for debugging
    app.final_dss_path = str(final_file)

# Function to extract fault currents from fault elements
def get_fault_element_currents() -> list[dict]:
    results = []

    # Iterate all circuit elements and pick those with class "Fault"
    for name in dss.Circuit.AllElementNames():
        if not name.lower().startswith("fault."):
            continue

        dss.Circuit.SetActiveElement(name)

        # CurrentsMagAng is [mag1, ang1, mag2, ang2, ...] (A, degrees)
        mags_angs = dss.CktElement.CurrentsMagAng()
        mags = mags_angs[0::2]  # take magnitudes only

        # bus1 is the first terminal bus name
        buses = dss.CktElement.BusNames()
        bus1 = buses[0] if buses else ""

        results.append({
            "fault_element": name,
            "bus1": bus1,
            "phase_current_mags_A": mags,
            "max_phase_current_A": max(mags) if mags else None,
        })

    return results

# --- TKINTER APP SETUP AND FUNCTIONALITY ---
# Define the app class
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("DER Arc Flash Analysis Tool")
        self.geometry("1100x700")

        # Set up navigation for menu options
        nav_frame = tk.Frame(self, bg="#123", height=50)
        nav_frame.pack(side="top", fill="x")

        buttons = [
            ("System Model", self.show_system_model),
            ("DER Settings", self.show_der_settings),
            ("Fault Scenario", self.show_fault_scenario),
            ("Run Simulation", self.show_run_sim),
            ("Results", self.show_results),
        ]

        for text, command in buttons:
            btn = tk.Button(
                nav_frame,
                text=text,
                command=command,
                fg="black",
                bg="#333",
                activebackground="#444",
                relief="flat",
                padx=20,
                pady=10,
            )
            btn.pack(side="left", padx=5, pady=5)

        # actual page area
        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill="both", expand=True)

        self.pages = {}

        for PageClass in (
            SystemModelPage,
            DERSettingsPage,
            FaultScenarioPage,
            RunSimulationPage,
            ResultsPage,
        ):
            page = PageClass(self.container)
            self.pages[PageClass] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_page(SystemModelPage)

        # Add variables to store dss commands
        self.system_master_path = ""
        self.build_text = ""
        self.run_text = ""
        self.der_text = ""
        self.fault_text = ""
        self.final_dss_text = ""
        self.final_dss_path = ""
        self.final_path = ""

    def show_page(self, page_class):
        page = self.pages[page_class]
        page.tkraise()

    # navigation commands
    def show_system_model(self):
        self.show_page(SystemModelPage)

    def show_der_settings(self):
        self.show_page(DERSettingsPage)

    def show_fault_scenario(self):
        self.show_page(FaultScenarioPage)

    def show_run_sim(self):
        self.show_page(RunSimulationPage)

    def show_results(self):
        self.show_page(ResultsPage)

# set up page frames
class SystemModelPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")

        title = tk.Label(self, text="System Model Interface", font=("Arial", 20), bg="white", fg="black")
        title.pack(pady=20)

        # inputs
        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        # Select file button
        tk.Label(form, text="System File:", bg="white", fg="black").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.file_label = tk.Label(form, text="No file selected", bg="white", fg="black")
        self.file_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        load_btn = tk.Button(form, text="Select System Model", command=self.load_file, fg="black", bg="#EEE")
        load_btn.grid(row=0, column=2, padx=5, pady=5)

        # Summary output box
        summary_frame = tk.LabelFrame(self, text="Model Summary", bg="white", fg="black")
        summary_frame.pack(fill="both", expand=False, padx=20, pady=15)

        self.summary_text = tk.Text(summary_frame, height=12, wrap="word")
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.summary_text.insert("1.0", "No model loaded yet.\n")
        self.summary_text.config(state="disabled")


    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select System Model File",
            filetypes=[("All Files", "*.*"), ("CSV Files", "*.csv"), ("JSON Files", "*.json"), ("OpenDSS Files", "*.dss")],
        )
        if file_path.lower().endswith(".dss"):
            self.file_label.config(text=file_path, fg="black")
            summary = compile_and_summarize(file_path)
            print(summary)
            
        if not file_path.lower().endswith(".dss"):
            self.summary_text.config(state="normal")
            self.summary_text.delete("1.0", "end")
            self.summary_text.insert("1.0", "Loaded non-DSS file. DSS compile not run.\n")
            self.summary_text.config(state="disabled")
            
            # Update summary text
        summary_text = (
            "Inputted System Model Summary:\n\n"
            f"Circuit:          {summary.get('circuit_name')}\n"
            f"Buses:            {summary.get('num_buses')}\n"
            f"Transformers:     {summary.get('num_transformers')}\n"
            f"Loads:            {summary.get('num_loads')}\n"
            f"Converged:        {summary.get('converged')}\n\n"
            f"System model successfully compiled.\nPlease add DER Settings and Fault Scenario before running simulation."
        )

        # Update summary text information with uploaded info
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", summary_text)
        self.summary_text.config(state="disabled")

        # Get build and run commands as strings
        app.build_text, app.run_text = split_build_and_run(read_dss_text(file_path))

class DERSettingsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")

        title = tk.Label(self, text="DER & Protection Settings", font=("Arial", 20), bg="white", fg="black")
        title.pack(pady=20)

        # inputs
        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        # dropdown to select inverter type (grid-following or grid-forming)
        tk.Label(form, text="Inverter Type:", bg="white", fg="black").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.model_type = ttk.Combobox(
            form,
            values=["GFL" , "GFM"],
            state="readonly",
            width=15,
        )
        self.model_type.current(0)
        self.model_type.grid(row=0, column=1, padx=5, pady=5)

        # load file button
        tk.Label(form, text="Inverter File:", bg="white", fg="black").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.file_label = tk.Label(form, text="No file selected", bg="white", fg="black")
        self.file_label.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        load_btn = tk.Button(form, text="Load DER Model", command=self.load_der_file, fg="black", bg="#EEE")
        load_btn.grid(row=1, column=2, padx=5, pady=5)

        # Summary box
        summary_frame = tk.LabelFrame(self, text="DER Summary", bg="white", fg="black")
        summary_frame.pack(fill="both", expand=False, padx=20, pady=15)

        self.der_summary_text = tk.Text(summary_frame, height=12, wrap="word")
        self.der_summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.der_summary_text.insert("1.0", "No DER file loaded yet.\n")
        self.der_summary_text.config(state="disabled")

    def load_der_file(self):
        der_path = filedialog.askopenfilename(
            title="Select DER Settings File",
            filetypes=[("OpenDSS Files", "*.dss"), ("All Files", "*.*")]
        )
        if not der_path:
            return

        app = self.winfo_toplevel()
        app.der_text = Path(der_path).read_text(encoding="utf-8", errors="replace")

        summary = summarize_der_dss_text(app.der_text)
        summary_str = der_summary_to_string(der_path, summary)

        self.der_summary_text.config(state="normal")
        self.der_summary_text.delete("1.0", "end")
        self.der_summary_text.insert("1.0", summary_str)
        self.der_summary_text.config(state="disabled")

class DERSettingsManualPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")

        title = tk.Label(self, text="DER & Protection Settings", font=("Arial", 20), bg="white", fg="black")
        title.pack(pady=20)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        # dropdown for DER type
        tk.Label(form, text="DER Type:", bg="white", fg="black").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.der_type = ttk.Combobox(
            form,
            values=["PV Inverter", "Battery Inverter", "Generic Inverter"],
            state="readonly",
            width=20,
        )
        self.der_type.current(0)
        self.der_type.grid(row=0, column=1, padx=5, pady=5)

        # dropdown for bus selection (pulls from system model)
        tk.Label(form, text="Connected Bus:", bg="white", fg="black").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.der_bus = ttk.Combobox(
            form,
            values=["Bus1", "Bus2", "Bus3"],
            state="readonly",
            width=20,
        )
        self.der_bus.current(0)
        self.der_bus.grid(row=1, column=1, padx=5, pady=5)

        # rated power input
        tk.Label(form, text="Rated Power (kW):", bg="white", fg="black").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.der_power = tk.Entry(form, width=10, fg="black", bg="white")
        self.der_power.insert(0, "500")
        self.der_power.grid(row=2, column=1, padx=5, pady=5)

        # dropdown for fault current limitation
        tk.Label(form, text="Fault Current Limit (pu):", bg="white", fg="black").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.der_fault_limit = ttk.Combobox(
            form,
            values=["1.1", "1.2", "1.3"],
            state="readonly",
            width=10,
        )
        self.der_fault_limit.current(1)
        self.der_fault_limit.grid(row=3, column=1, padx=5, pady=5)

        add_btn = tk.Button(form, text="Add DER", command=self.add_der, fg="black", bg="#EEE")
        add_btn.grid(row=4, column=0, columnspan=2, pady=10)

        self.der_list = tk.Listbox(self, width=60, height=8, fg="black")
        self.der_list.pack(pady=10)

    def add_der(self):
        der_info = f"{self.der_type.get()} @ {self.der_bus.get()} | {self.der_power.get()} kW | I_limit={self.der_fault_limit.get()} pu"
        self.der_list.insert(tk.END, der_info)


class FaultScenarioPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")

        title = tk.Label(self, text="Fault Scenario Selection", font=("Arial", 20), bg="white", fg="black")
        title.pack(pady=20)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        # Select file button
        tk.Label(form, text="Fault Scenario File:", bg="white", fg="black").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.file_label = tk.Label(form, text="No file selected", bg="white", fg="black")
        self.file_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        load_btn = tk.Button(form, text="Select Fault Scenario File", command=self.load_fault_file, fg="black", bg="#EEE")
        load_btn.grid(row=0, column=2, padx=5, pady=5)

        # Summary box
        summary_frame = tk.LabelFrame(self, text="Fault Scenario Summary", bg="white", fg="black")
        summary_frame.pack(fill="both", expand=False, padx=20, pady=15)

        self.der_summary_text = tk.Text(summary_frame, height=12, wrap="word")
        self.der_summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.der_summary_text.insert("1.0", "No Fault Scenario file loaded yet.\n")
        self.der_summary_text.config(state="disabled")

    def load_fault_file(self):
        fault_path = filedialog.askopenfilename(
            title="Select Fault Scenario File",
            filetypes=[("OpenDSS Files", "*.dss"), ("All Files", "*.*")]
        )
        if not fault_path:
            return

        app = self.winfo_toplevel()
        app.fault_text = Path(fault_path).read_text(encoding="utf-8", errors="replace")

        summary = summarize_fault_dss_text(app.fault_text)
        summary_str = fault_summary_to_string(fault_path, summary)

        self.der_summary_text.config(state="normal")
        self.der_summary_text.delete("1.0", "end")
        self.der_summary_text.insert("1.0", summary_str)
        self.der_summary_text.config(state="disabled")


class RunSimulationPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")

        title = tk.Label(self, text="Run Simulation (Octave Integration)", font=("Arial", 20), bg="white", fg="black")
        title.pack(pady=20)

        self.status = tk.Label(self, text="Ready to run simulation.", bg="white", fg="black")
        self.status.pack(pady=10)

        run_btn = tk.Button(self, text="Run Dynamic Simulation", command=self.run_sim, fg="black", bg="#EEE")
        run_btn.pack(pady=10)

    def run_sim(self):
        run_simulation()
        self.status.config(text=f"{get_fault_element_currents()}", fg="black")


class ResultsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")

        title = tk.Label(self, text="Results & Arc-Flash Outputs", font=("Arial", 20), bg="white", fg="black")
        title.pack(pady=20)

        self.results_label = tk.Label(self, text={"Results will be shown here (plots, tables, etc.)."}, bg="white", fg="black")
        self.results_label.pack(pady=10)



# launch program
if __name__ == "__main__":
    app = App()
    app.mainloop()
