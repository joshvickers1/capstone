# --- Defined earlier in GUI ---
ARC_GAP_MM = None              # e.g. 32
ARC_ENCLOSURE = None           # "VCB", "HCB", "VOA", "HOA"
WORKING_DISTANCE_MM = None    # e.g. 457
IS_GROUNDED = None            # True / False
CLEARING_TIME_S = None        # e.g. 0.08

# ------------------------------------------------------------ #

import numpy as np
import opendssdirect as dss
import matplotlib.pyplot as plt

# PPE Limits (IEEE 1584)

PPE_LIMITS = {
    "PPE Category 1": 4,
    "PPE Category 2": 8,
    "PPE Category 3": 25,
    "PPE Category 4": 40
}


# OpenDSS Extraction

def extract_arcflash_inputs(bus_name):
    dss.Circuit.SetActiveBus(bus_name)
    V_kV = dss.Bus.kVBase()   # kV base
    I_bf = dss.Bus.Isc()     # bolted fault current (kA)
    return V_kV, I_bf



# IEEE 1584-2018 Core

def ieee1584_arcing_current(I_bf, V_kV, gap_mm, enclosure):
    COEFFS = {
        "VCB": (-0.153, 0.662, 0.0966),
        "HCB": (-0.153, 0.662, 0.0966),
        "VOA": (-0.792, 0.662, 0.0966),
        "HOA": (-0.792, 0.662, 0.0966),
    }

    k1, k2, k3 = COEFFS[enclosure]

    log_Ia = (
        k1 +
        k2 * np.log10(I_bf) +
        k3 * np.log10(V_kV * 1000) +
        0.00402 * gap_mm
    )

    return 10 ** log_Ia


def ieee1584_incident_energy(Ia, V_kV, gap_mm, clearing_time_s, working_distance_mm):
    En = 10 ** (
        -0.555 +
        1.081 * np.log10(Ia) +
        0.0011 * gap_mm
    )

    Cf = 1.0 if V_kV >= 1.0 else 1.5

    return Cf * En * (clearing_time_s / 0.2) * (610 / working_distance_mm) ** 2



# PPE Classification

def ppe_category(energy_cal_cm2):
    if energy_cal_cm2 <= 1.2:
        return "Below arc-flash threshold (No PPE)"
    elif energy_cal_cm2 <= 4:
        return "PPE Category 1"
    elif energy_cal_cm2 <= 8:
        return "PPE Category 2"
    elif energy_cal_cm2 <= 25:
        return "PPE Category 3"
    elif energy_cal_cm2 <= 40:
        return "PPE Category 4"
    else:
        return "Above PPE Category 4 (Dangerous)"



# Plot Arcing Current + PPE Safe/Unsafe

def plot_arcflash_ppe(V_kV, gap_mm, clearing_time_s, working_distance_mm, enclosure, ppe_limit):
    Ibf_range = np.linspace(1, 50, 300)

    Ia_vals = np.array([
        ieee1584_arcing_current(i, V_kV, gap_mm, enclosure)
        for i in Ibf_range
    ])

    energies = np.array([
        ieee1584_incident_energy(Ia, V_kV, gap_mm, clearing_time_s, working_distance_mm)
        for Ia in Ia_vals
    ])

    safe = energies <= ppe_limit
    unsafe = energies > ppe_limit

    plt.figure(figsize=(9, 5))
    plt.plot(Ibf_range, Ia_vals, label="Arcing Current (kA)")
    plt.fill_between(Ibf_range, 0, Ia_vals, where=safe, alpha=0.3, label="Safe Region")
    plt.fill_between(Ibf_range, 0, Ia_vals, where=unsafe, alpha=0.3, label="Unsafe Region")

    plt.xlabel("Bolted Fault Current (kA)")
    plt.ylabel("Arcing Current (kA)")
    plt.title("Arcing Current vs PPE Safe/Unsafe Region")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()



# Main GUI-Triggered Function

def run_arcflash_analysis(bus_name):
    # These are expected to be set earlier by GUI
    assert ARC_GAP_MM is not None
    assert ARC_ENCLOSURE is not None
    assert WORKING_DISTANCE_MM is not None
    assert CLEARING_TIME_S is not None

    V_kV, I_bf = extract_arcflash_inputs(bus_name)

    Ia = ieee1584_arcing_current(
        I_bf,
        V_kV,
        ARC_GAP_MM,
        ARC_ENCLOSURE
    )

    E = ieee1584_incident_energy(
        Ia,
        V_kV,
        ARC_GAP_MM,
        CLEARING_TIME_S,
        WORKING_DISTANCE_MM
    )

    ppe = ppe_category(E)

    print("===== ARC FLASH RESULTS =====")
    print(f"Bus: {bus_name}")
    print(f"Voltage: {V_kV:.3f} kV")
    print(f"Bolted Fault Current: {I_bf:.2f} kA")
    print(f"Arcing Current: {Ia:.2f} kA")
    print(f"Incident Energy: {E:.2f} cal/cm^2")
    print(f"PPE Requirement: {ppe}")

    if ppe in PPE_LIMITS:
        plot_arcflash_ppe(
            V_kV,
            ARC_GAP_MM,
            CLEARING_TIME_S,
            WORKING_DISTANCE_MM,
            ARC_ENCLOSURE,
            PPE_LIMITS[ppe]
        )