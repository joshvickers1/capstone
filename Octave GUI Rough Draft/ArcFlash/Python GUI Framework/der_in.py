import opendssdirect as dss

inv_type = "VCCS"

dss.Basic.ClearAll()
dss.Text.Command(r'Compile "IEEE13Nodeckt.dss"')

if inv_type == "VCCS": # VOLTAGE CONTROLLED CURRENT SOURCE
    # Define voltage-current characteristic
    dss.Text.Command("""
    New XYcurve.VIcurve npts=3
    ~ xarray=[0.8 1.0 1.2]
    ~ yarray=[1.2 1.0 0.8]
    """)

    # Create VSCCS inverter
    dss.Text.Command("""
    New VSCCS.Inv1
    ~ bus1=634.1.2.3
    ~ phases=3
    ~ kv=4.16
    ~ kW=500
    ~ kvar=0
    ~ vcurve=VIcurve
    ~ imax=1.2
    ~ model=1
    """)

    # Dynamics mode (time-step simulation)
    dss.Text.Command("Set mode=dynamics stepsize=0.0001 number=1000")
    dss.Solution.Solve()

elif inv_type == "CCS": # CONSTANT CURRENT SOURCE
    dss.Text.Command("""
    New Isource.InvI bus1=bus634.1.2.3 phases=3
      amps=100 angle=0 frequency=60
    """)

    dss.Solution.Solve()

elif inv_type == "VS":
    dss.Text.Command("""
    New Vsource.InvV bus1=bus634 phases=3 basekv=4.16 pu=1.0 angle=0
      model=Ideal
    """)