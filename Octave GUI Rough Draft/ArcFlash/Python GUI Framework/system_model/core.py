from dataclasses import dataclass, field
from typing import Dict, Optional

# set up data structures to keep things uniform

@dataclass
class Bus:
    bus_id: str
    kv: float


@dataclass
class Line:
    line_id: str
    from_bus: str
    to_bus: str
    r_ohm: float
    x_ohm: float


@dataclass
class Transformer:
    tx_id: str
    primary_bus: str
    secondary_bus: str
    primary_kv: float
    secondary_kv: float
    z_percent: float
    tap: Optional[float] = None


@dataclass
class SystemModel:
    buses: Dict[str, Bus] = field(default_factory=dict)
    lines: Dict[str, Line] = field(default_factory=dict)
    transformers: Dict[str, Transformer] = field(default_factory=dict)

    def validate(self) -> None:
        # make sure all lines have end points
        for line in self.lines.values():
            if line.from_bus not in self.buses:
                raise ValueError(
                    f"Line '{line.line_id}' references unknown from_bus '{line.from_bus}'."
                )
            if line.to_bus not in self.buses:
                raise ValueError(
                    f"Line '{line.line_id}' references unknown to_bus '{line.to_bus}'."
                )

        # Cmake sure all transformer buses exist
        for tx in self.transformers.values():
            if tx.primary_bus not in self.buses:
                raise ValueError(
                    f"Transformer '{tx.tx_id}' references unknown primary_bus '{tx.primary_bus}'."
                )
            if tx.secondary_bus not in self.buses:
                raise ValueError(
                    f"Transformer '{tx.tx_id}' references unknown secondary_bus '{tx.secondary_bus}'."
                )
