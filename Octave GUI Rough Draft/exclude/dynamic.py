from oct2py import Oct2Py
import numpy as np
import matplotlib.pyplot as plt

# Start Octave session
oc = Oct2Py()

# Parameters
I0 = 0.0          # initial current (A)
I_limit = 120.0   # max inverter fault current (A)
tau = 0.025       # time constant (s)
t_start = 0.0
t_end = 0.1

# Define the ODE function in Octave
oc.eval("""
function dIdt = inverter_dynamics(t, I, I_limit, tau)
    dIdt = -(1/tau) * (I - I_limit);
end
""")

# Time vector
t_eval = np.linspace(t_start, t_end, 1000)

# Call Octave's ode45
t, I = oc.ode45("inverter_dynamics", t_eval, I0, I_limit, tau)

# Convert I to a flat NumPy array
I = np.array(I).flatten()

# Plot result
plt.plot(t, I)
plt.xlabel("Time (s)")
plt.ylabel("Inverter Fault Current (A)")
plt.title("Inverter Dynamic Response During Fault (Octave ode45 via Python)")
plt.grid(True)
plt.tight_layout()
plt.show()
