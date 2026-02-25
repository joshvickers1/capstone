import pathlib

from .core import SystemModel, Bus, Line, Transformer

# make sure user has OpenDSS direct downloaded
try:
    import opendssdirect as dss
    HAS_DSS = True
except ImportError:
    HAS_DSS = False


class DssReader:
    """
    Loads a DSS (OpenDSS) model using opendssdirect, then extracts
    buses, lines, and transformers into a SystemModel.

    Assumes the provided path is a 'master' DSS file that sets up the circuit.
    """

    def __init__(self):
        if not HAS_DSS:
            raise ImportError(
                "opendssdirect is required for DssSystemModelLoader, but is not installed."
            )

    def load(self, dss_master_path: str) -> SystemModel:
        model = SystemModel()
        path = pathlib.Path(dss_master_path)

        if not path.exists():
            raise FileNotFoundError(f"DSS master file not found: {dss_master_path}")

        # Reset OpenDSS and compile the model
        dss.Basic.ClearAll()
        dss.Text.Command(f"compile '{path.as_posix()}'")

        # Check for errors
        error = dss.Error.Number()
        if error != 0:
            msg = dss.Error.Description()
            raise RuntimeError(
                f"Error compiling DSS file '{dss_master_path}': {msg}"
            )

        # -------- Buses --------
        for bus_name in dss.Circuit.AllBusNames():
            dss.Circuit.SetActiveBus(bus_name)
            kv_base = dss.Bus.kVBase()
            model.buses[bus_name] = Bus(
                bus_id=bus_name,
                kv=kv_base if kv_base is not None else 0.0,
            )

        # -------- Lines --------
        dss.Lines.First()
        while True:
            name = dss.Lines.Name()
            if not name:
                break

            from_bus = dss.Lines.Bus1().split('.')[0]
            to_bus = dss.Lines.Bus2().split('.')[0]
            r_ohm = dss.Lines.R1()
            x_ohm = dss.Lines.X1()
            length = dss.Lines.Length()
            linecode = dss.Lines.LineCode()

            model.lines[name] = Line(
                line_id=name,
                from_bus=from_bus,
                to_bus=to_bus,
                r_ohm=r_ohm,
                x_ohm=x_ohm,
                length=length,
                linecode=linecode or None,
            )

            if dss.Lines.Next() == 0:
                break

        # -------- Transformers --------
        dss.Transformers.First()
        while True:
            name = dss.Transformers.Name()
            if not name:
                break

            # Assume 2-winding transformer for now
            dss.Transformers.Wdg(1)
            primary_bus = dss.Transformers.Bus().split('.')[0]
            primary_kv = dss.Transformers.kV()

            dss.Transformers.Wdg(2)
            secondary_bus = dss.Transformers.Bus().split('.')[0]
            secondary_kv = dss.Transformers.kV()

            z_percent = dss.Transformers.XHL()
            tap = dss.Transformers.Tap()

            model.transformers[name] = Transformer(
                tx_id=name,
                primary_bus=primary_bus,
                secondary_bus=secondary_bus,
                primary_kv=primary_kv,
                secondary_kv=secondary_kv,
                z_percent=z_percent,
                tap=tap,
            )

            if dss.Transformers.Next() == 0:
                break

        model.validate()
        return model
