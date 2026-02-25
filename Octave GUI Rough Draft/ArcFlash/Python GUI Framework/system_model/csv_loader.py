import csv
import pathlib
from typing import Dict

# import structures from the core file
from .core import SystemModel, Bus, Line, Transformer

class CsvReader:
    
    # set required fields to make sure necessary information can be read
    REQUIRED_BUS_FIELDS = {"bus_id", "kv"}
    REQUIRED_LINE_FIELDS = {"line_id", "from_bus", "to_bus", "r_ohm", "x_ohm"}
    REQUIRED_TX_FIELDS = {
        "tx_id", "primary_bus", "secondary_bus", "primary_kv", "secondary_kv", "z_percent"
    }

    def load(self, csv_path: str) -> SystemModel:
        model = SystemModel()
        path = pathlib.Path(csv_path)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        with path.open("r", newline="") as f:
            reader = csv.DictReader(f)

            if "type" not in reader.fieldnames:
                raise ValueError("CSV must include a 'type' column indicating 'bus', 'line', or 'transformer'.")

            for row in reader:
                row_type = (row.get("type") or "").strip().lower()

                if not row_type:
                    # Skip empty or untyped rows
                    continue

                if row_type == "bus":
                    self._add_bus(model, row)
                elif row_type == "line":
                    self._add_line(model, row)
                elif row_type == "transformer":
                    self._add_transformer(model, row)
                else:
                    raise ValueError(f"Unknown row type '{row_type}' in CSV.")

        model.validate()
        return model

    def _add_bus(self, model: SystemModel, row: Dict[str, str]) -> None:
        missing = self.REQUIRED_BUS_FIELDS - row.keys()
        if missing:
            raise ValueError(f"Bus row missing required fields: {missing}")

        bus = Bus(
            bus_id=str(row["bus_id"]),
            kv=float(row["kv"]),
            zone=row.get("zone") or None,
        )
        if bus.bus_id in model.buses:
            raise ValueError(f"Duplicate bus_id found in CSV: {bus.bus_id}")
        model.buses[bus.bus_id] = bus

    def _add_line(self, model: SystemModel, row: Dict[str, str]) -> None:
        missing = self.REQUIRED_LINE_FIELDS - row.keys()
        if missing:
            raise ValueError(f"Line row missing required fields: {missing}")

        line = Line(
            line_id=str(row["line_id"]),
            from_bus=str(row["from_bus"]),
            to_bus=str(row["to_bus"]),
            r_ohm=float(row["r_ohm"]),
            x_ohm=float(row["x_ohm"]),
            length=float(row["length"]) if row.get("length") else None,
            linecode=row.get("linecode") or None,
        )
        if line.line_id in model.lines:
            raise ValueError(f"Duplicate line_id found in CSV: {line.line_id}")
        model.lines[line.line_id] = line

    def _add_transformer(self, model: SystemModel, row: Dict[str, str]) -> None:
        missing = self.REQUIRED_TX_FIELDS - row.keys()
        if missing:
            raise ValueError(f"Transformer row missing required fields: {missing}")

        tx = Transformer(
            tx_id=str(row["tx_id"]),
            primary_bus=str(row["primary_bus"]),
            secondary_bus=str(row["secondary_bus"]),
            primary_kv=float(row["primary_kv"]),
            secondary_kv=float(row["secondary_kv"]),
            z_percent=float(row["z_percent"]),
            tap=float(row["tap"]) if row.get("tap") else None,
        )
        if tx.tx_id in model.transformers:
            raise ValueError(f"Duplicate tx_id found in CSV: {tx.tx_id}")
        model.transformers[tx.tx_id] = tx
