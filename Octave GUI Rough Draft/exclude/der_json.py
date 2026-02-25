# der_storage.py

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


# ---------------------------
# Low-level config dataclasses
# ---------------------------

@dataclass
class REGCConfig:
    model: str = "REGC_A"
    imax: float = 1.2
    imax_fault: Optional[float] = None
    r_source_pu: float = 0.01
    x_source_pu: float = 0.12
    iq_priority: str = "reactive"  # "reactive" or "active"

    # PLL (simplified)
    kp_pll: float = 20.0
    ki_pll: float = 200.0
    wmax: float = 2.0
    wmin: float = -2.0

    def effective_imax_fault(self) -> float:
        """If imax_fault not provided, fall back to imax."""
        return self.imax_fault if self.imax_fault is not None else self.imax


@dataclass
class REECConfig:
    model: str = "REEC_A"
    vref_pu: float = 1.0
    qref_pu: float = 0.0

    # Voltage-dependent reactive current
    kqv: float = 7.5
    vdip_pu: float = 0.9
    vup_pu: float = 1.1
    iqmax_pu: float = 1.1
    iqmin_pu: float = -1.1

    # Active power limits
    pmax_pu: float = 1.0
    pmin_pu: float = 0.0

    # Mode flags (simplified)
    pf_flag: int = 0
    pq_flag: int = 1
    vq_flag: int = 0


@dataclass
class VRTPoint:
    voltage_pu: float
    max_time_s: float


@dataclass
class FRTPoint:
    frequency_hz: float
    max_time_s: float


@dataclass
class RideThroughConfig:
    vrt_curve: List[VRTPoint] = field(default_factory=list)
    frt_curve: List[FRTPoint] = field(default_factory=list)


# ---------------------------
# High-level DER dataclass
# ---------------------------

@dataclass
class DER:
    """Internal representation of a single DER / inverter-based resource."""

    der_id: str
    der_type: str              # e.g. "PV", "BESS", "WIND"
    connection_bus: str        # e.g. "BUS3"

    mva_rating: float
    kv_ll: float               # line-to-line nominal voltage at DER terminal

    # Prefault operating point
    pref_MW: float
    qref_MVAR: float = 0.0
    power_factor: Optional[float] = None

    regc: REGCConfig = field(default_factory=REGCConfig)
    reec: REECConfig = field(default_factory=REECConfig)
    ride_through: RideThroughConfig = field(default_factory=RideThroughConfig)

    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------- validation & utility methods -------------

    def validate(self) -> None:
        """
        Basic sanity checks. Raise ValueError if configuration is clearly invalid.
        You can expand this over time.
        """
        if self.mva_rating <= 0:
            raise ValueError("mva_rating must be > 0")

        if self.kv_ll <= 0:
            raise ValueError("kv_ll must be > 0")

        if not self.connection_bus:
            raise ValueError("connection_bus must be non-empty")

        if self.regc.imax <= 0:
            raise ValueError("regc.imax must be > 0")

        if self.reec.iqmax_pu < 0:
            raise ValueError("reec.iqmax_pu should be >= 0")

        # You can add range checks for vdip/vup, kqv, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Serialize DER to a plain dict (JSON-serializable)."""
        d = asdict(self)
        # Convert nested RideThrough curves to dicts explicitly (already dict-like, but being explicit)
        d["ride_through"]["vrt_curve"] = [
            asdict(p) for p in self.ride_through.vrt_curve
        ]
        d["ride_through"]["frt_curve"] = [
            asdict(p) for p in self.ride_through.frt_curve
        ]
        return d

    def to_sim_payload(self) -> Dict[str, Any]:
        """
        Return a minimal payload that the dynamic simulation engine (Octave)
        actually needs. This is what you pass into your simulation_runner.
        """
        regc = self.regc
        reec = self.reec
        rt = self.ride_through

        return {
            "der_id": self.der_id,
            "type": self.der_type,
            "connection_bus": self.connection_bus,
            "mva_rating": self.mva_rating,
            "kv_ll": self.kv_ll,
            "pref_MW": self.pref_MW,
            "qref_MVAR": self.qref_MVAR,
            "power_factor": self.power_factor,

            "regc": {
                "model": regc.model,
                "imax": regc.imax,
                "imax_fault": regc.effective_imax_fault(),
                "r_source_pu": regc.r_source_pu,
                "x_source_pu": regc.x_source_pu,
                "iq_priority": regc.iq_priority,
                "kp_pll": regc.kp_pll,
                "ki_pll": regc.ki_pll,
                "wmax": regc.wmax,
                "wmin": regc.wmin,
            },

            "reec": {
                "model": reec.model,
                "vref_pu": reec.vref_pu,
                "qref_pu": reec.qref_pu,
                "kqv": reec.kqv,
                "vdip_pu": reec.vdip_pu,
                "vup_pu": reec.vup_pu,
                "iqmax_pu": reec.iqmax_pu,
                "iqmin_pu": reec.iqmin_pu,
                "pmax_pu": reec.pmax_pu,
                "pmin_pu": reec.pmin_pu,
                "pf_flag": reec.pf_flag,
                "pq_flag": reec.pq_flag,
                "vq_flag": reec.vq_flag,
            },

            "ride_through": {
                "vrt_curve": [asdict(p) for p in rt.vrt_curve],
                "frt_curve": [asdict(p) for p in rt.frt_curve],
            }
        }


# ---------------------------
# DER storage / loader helper
# ---------------------------

class DERStorage:
    """
    Helper to construct DER objects from JSON or dicts and
    act as a registry if you have multiple DERs.
    """

    def __init__(self) -> None:
        self._ders: Dict[str, DER] = {}

    # ---- construction helpers ----

    def from_json_file(self, der_id: str, path: str | Path) -> DER:
        data = self._load_json(path)
        der = self.from_dict(der_id, data)
        return der

    def from_dict(self, der_id: str, data: Dict[str, Any]) -> DER:
        """
        Build a DER object from a dict (e.g., loaded from JSON).
        This is where you map JSON keys into your dataclasses.
        """
        der_type = data["der_type"]
        connection_bus = data["connection_bus"]
        mva_rating = data["mva_rating"]
        kv_ll = data.get("kv", data.get("kv_ll"))

        pref_MW = data.get("pref_MW", 0.0)
        qref_MVAR = data.get("qref_MVAR", 0.0)
        power_factor = data.get("power_factor")

        # REGC config
        regc_data = data.get("regc", {})
        regc = REGCConfig(
            model=regc_data.get("model", "REGC_A"),
            imax=regc_data.get("imax", 1.2),
            imax_fault=regc_data.get("imax_fault"),
            r_source_pu=regc_data.get("r_source_pu", 0.01),
            x_source_pu=regc_data.get("x_source_pu", 0.12),
            iq_priority=regc_data.get("iq_priority", "reactive"),
            kp_pll=regc_data.get("kp_pll", 20.0),
            ki_pll=regc_data.get("ki_pll", 200.0),
            wmax=regc_data.get("wmax", 2.0),
            wmin=regc_data.get("wmin", -2.0),
        )

        # REEC config
        reec_data = data.get("reec", {})
        reec = REECConfig(
            model=reec_data.get("model", "REEC_A"),
            vref_pu=reec_data.get("vref_pu", 1.0),
            qref_pu=reec_data.get("qref_pu", 0.0),
            kqv=reec_data.get("kqv", 7.5),
            vdip_pu=reec_data.get("vdip_pu", 0.9),
            vup_pu=reec_data.get("vup_pu", 1.1),
            iqmax_pu=reec_data.get("iqmax_pu", 1.1),
            iqmin_pu=reec_data.get("iqmin_pu", -1.1),
            pmax_pu=reec_data.get("pmax_pu", 1.0),
            pmin_pu=reec_data.get("pmin_pu", 0.0),
            pf_flag=reec_data.get("pf_flag", 0),
            pq_flag=reec_data.get("pq_flag", 1),
            vq_flag=reec_data.get("vq_flag", 0),
        )

        # Ride-through config
        rt_data = data.get("ride_through", {})
        vrt_raw = rt_data.get("vrt_curve", [])
        frt_raw = rt_data.get("frt_curve", [])

        vrt_curve = [
            VRTPoint(voltage_pu=pt["voltage_pu"], max_time_s=pt["max_time_s"])
            for pt in vrt_raw
        ]
        frt_curve = [
            FRTPoint(frequency_hz=pt["frequency_hz"], max_time_s=pt["max_time_s"])
            for pt in frt_raw
        ]
        ride_through = RideThroughConfig(vrt_curve=vrt_curve, frt_curve=frt_curve)

        der = DER(
            der_id=der_id,
            der_type=der_type,
            connection_bus=connection_bus,
            mva_rating=mva_rating,
            kv_ll=kv_ll,
            pref_MW=pref_MW,
            qref_MVAR=qref_MVAR,
            power_factor=power_factor,
            regc=regc,
            reec=reec,
            ride_through=ride_through,
            metadata=data.get("metadata", {})
        )

        der.validate()
        self._ders[der_id] = der
        return der

    # ---- query methods ----

    def get(self, der_id: str) -> DER:
        return self._ders[der_id]

    def all_ders(self) -> Dict[str, DER]:
        return dict(self._ders)

    # ---- internal helpers ----

    @staticmethod
    def _load_json(path: str | Path) -> Dict[str, Any]:
        path = Path(path)
        with path.open("r") as f:
            return json.load(f)
