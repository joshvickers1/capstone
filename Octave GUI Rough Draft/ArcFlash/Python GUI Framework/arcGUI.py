import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("DER Arc Flash Analysis Tool")
        self.geometry("1100x700")

        # set up navigation for menu options
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

        # dropdown to select model type
        tk.Label(form, text="Model Type:", bg="white", fg="black").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.model_type = ttk.Combobox(
            form,
            values=["CSV", "JSON", "OpenDSS"],
            state="readonly",
            width=15,
        )
        self.model_type.current(0)
        self.model_type.grid(row=0, column=1, padx=5, pady=5)

        # load file button
        tk.Label(form, text="System File:", bg="white", fg="black").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.file_label = tk.Label(form, text="No file selected", bg="white", fg="black")
        self.file_label.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        load_btn = tk.Button(form, text="Load System Model", command=self.load_file, fg="black", bg="#EEE")
        load_btn.grid(row=1, column=2, padx=5, pady=5)

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select System Model File",
            filetypes=[("All Files", "*.*"), ("CSV Files", "*.csv"), ("JSON Files", "*.json"), ("OpenDSS Files", "*.dss")],
        )
        if file_path:
            self.file_label.config(text=file_path, fg="black")

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

        load_btn = tk.Button(form, text="Load DER Model", command=self.load_file, fg="black", bg="#EEE")
        load_btn.grid(row=1, column=2, padx=5, pady=5)

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Select DER Model File",
            filetypes=[("All Files", "*.*"), ("CSV Files", "*.csv"), ("JSON Files", "*.json"), ("OpenDSS Files", "*.dss")],
        )
        if file_path:
            self.file_label.config(text=file_path, fg="black")

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

        # dropdown for fault location
        tk.Label(form, text="Fault Bus:", bg="white", fg="black").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.fault_bus = ttk.Combobox(form, values=["Bus1", "Bus2", "Bus3"], state="readonly", width=20)
        self.fault_bus.current(0)
        self.fault_bus.grid(row=0, column=1, padx=5, pady=5)

        # dropdown for fault type
        tk.Label(form, text="Fault Type:", bg="white", fg="black").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.fault_type = ttk.Combobox(form, values=["3-Phase", "SLG", "LL", "LLG"], state="readonly", width=20)
        self.fault_type.current(0)
        self.fault_type.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form, text="Fault Duration (s):", bg="white", fg="black").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.fault_res = tk.Entry(form, width=10, fg="black", bg="white")
        self.fault_res.insert(0, "0.01")
        self.fault_res.grid(row=2, column=1, padx=5, pady=5)


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
        self.status.config(text="(Placeholder) Simulation would run here.", fg="black")


class ResultsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")

        title = tk.Label(self, text="Results & Arc-Flash Outputs", font=("Arial", 20), bg="white", fg="black")
        title.pack(pady=20)

        self.results_label = tk.Label(self, text="Results will be shown here (plots, tables, etc.).", bg="white", fg="black")
        self.results_label.pack(pady=10)


# launch program
if __name__ == "__main__":
    app = App()
    app.mainloop()
