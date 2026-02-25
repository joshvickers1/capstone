# import functions from each module
from .core import Bus, Line, Transformer, SystemModel
from .csv_loader import CsvReader
from .json_loader import JsonReader
from .dss_loader import DssReader

# if file type is valid, return system model object
def load_system_model(path: str, fmt: str) -> SystemModel:
    fmt = fmt.lower()
    if fmt == "csv":
        return CsvReader().load(path)
    elif fmt == "json":
        return JsonReader().load(path)
    elif fmt == "dss":
        return DssReader().load(path)
    else:
        raise ValueError(f"Unsupported file type: '{fmt}'")