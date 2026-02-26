import os
from pathlib import Path
import opendssdirect as dss

# Define path
master_path = r"IEEE13Nodeckt.dss"

# Compile model
dss.Text.Command(f'Compile "{str(master_path)}"')

# If OpenDSS reports an error, surface it immediately
if dss.Error.Number() != 0:
    err = dss.Error.Description()
    raise RuntimeError(f"OpenDSS compile error: {err}")

# --- Summary counts ---
summary = {
    "master_file": str(master_path),
    "circuit_name": dss.Circuit.Name(),
    "num_buses": dss.Circuit.NumBuses(),
    "num_nodes": dss.Circuit.NumNodes(),
    "num_loads": dss.Loads.Count(),
    "num_transformers": dss.Transformers.Count(),
    # optional extras (often handy):
    "num_lines": dss.Lines.Count(),
    "num_capacitors": dss.Capacitors.Count(),
    "num_generators": dss.Generators.Count(),
    "converged": bool(dss.Solution.Converged()),
    }

print(summary)