import json
import pathlib

from .core import SystemModel, Bus, Line, Transformer


class JsonReader:
    def load(self, json_path: str) -> SystemModel:
        model = SystemModel()
        path = pathlib.Path(json_path)

        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with path.open("r") as f:
            data = json.load(f)

        buses = data.get("buses", [])
        lines = data.get("lines", [])
        transformers = data.get("transformers", [])

        # create bus object from dictionary and add to SystemModel
        for b in buses:
            bus_id = str(b["bus_id"])
            if bus_id in model.buses:
                raise ValueError(f"Duplicate bus_id in JSON: {bus_id}")
            model.buses[bus_id] = Bus(
                bus_id=bus_id,
                kv=float(b["kv"]),
                zone=b.get("zone"),
            )

        # Lines
        for l in lines:
            line_id = str(l["line_id"])
            if line_id in model.lines:
                raise ValueError(f"Duplicate line_id in JSON: {line_id}")
            model.lines[line_id] = Line(
                line_id=line_id,
                from_bus=str(l["from_bus"]),
                to_bus=str(l["to_bus"]),
                r_ohm=float(l["r_ohm"]),
                x_ohm=float(l["x_ohm"]),
                length=float(l["length"]) if l.get("length") else None,
                linecode=l.get("linecode"),
            )

        # Transformers
        for t in transformers:
            tx_id = str(t["tx_id"])
            if tx_id in model.transformers:
                raise ValueError(f"Duplicate tx_id in JSON: {tx_id}")
            model.transformers[tx_id] = Transformer(
                tx_id=tx_id,
                primary_bus=str(t["primary_bus"]),
                secondary_bus=str(t["secondary_bus"]),
                primary_kv=float(t["primary_kv"]),
                secondary_kv=float(t["secondary_kv"]),
                z_percent=float(t["z_percent"]),
                tap=float(t["tap"]) if t.get("tap") else None,
            )

        model.validate()
        return model
