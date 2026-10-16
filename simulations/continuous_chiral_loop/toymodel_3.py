import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- 1. FUNDAMENTAL CONSTANTS & FLOW PHYSICS ---
k0_base = 25.0        # L/(mol*s)
k_cat = 15.0          # 1/s
K_A = 1000.0          # L/mol
K_B = 1000.0          # L/mol
K_inh_base = 120.0    # L/mol

P_D_bed = 0.5         # mol/L
P_L_bed = 0.005       # ee_bed = 98%

V_reactor = 1.0       # L
F_feed_max = 1e-4     # L/s (0.1 mL/s)
A_feed = 0.5          # M
B_feed = 0.5          # M
R_prod = 0.98         # OSN membrane rejection coefficient
F_bleed = 1e-5        # L/s

# Hydraulic & Osmotic Pressure Parameters
mu_solvent = 1.0e-3   # Pa*s
channel_L = 1.0       # m
d_hydraulic = 5e-4    # m (500 micrometers)
P_max_membrane = 30e5 # 30 bar = 3e6 Pa
alpha_shear = 5.0     # s/m

R_gas = 8.314         # J/(mol*K)
Temp_K = 298.15       # 25 °C (298.15 K)

def calc_friction_dp(v):
    # Hagen-Poiseuille friction pressure drop (Pa)
    return (32.0 * mu_solvent * channel_L / (d_hydraulic**2)) * v

def calc_osmotic_pressure(conc_diff_M):
    # van 't Hoff osmotic pressure: Delta_pi = Delta_C * R * T (Pa)
    # conc_diff_M converted from mol/L to mol/m^3 (* 1000)
    return (conc_diff_M * 1000.0) * R_gas * Temp_K

# --- 2. SYSTEM ODE EQUATIONS ---
def make_system_ode(v_loop):
    K_inh_eff = K_inh_base / (1.0 + alpha_shear * v_loop)
    
    def ode(t, y):
        A, B, D, L = max(y[0], 0), max(y[1], 0), max(y[2], 0), max(y[3], 0)
        
        # Adaptive Dosing Controller (Smooth sigmoid protecting 5e-5 M ceiling concentration)
        A_thresh = 5e-5
        F_in = F_feed_max / (1.0 + np.exp((A - A_thresh) / (0.15 * A_thresh)))
        F_perm = max(F_in - F_bleed, 0)
        
        denom = 1.0 + K_A * A + K_B * B + K_inh_eff * (D + L)
        theta_A = (K_A * A) / denom
        theta_B = (K_B * B) / denom
        
        r_rac = k0_base * A * B
        r_cat_D = k_cat * P_D_bed * theta_A * theta_B
        r_cat_L = k_cat * P_L_bed * theta_A * theta_B
        
        loss_A = (F_perm * (1.0 - 0.05) * A + F_bleed * A) / V_reactor
        loss_B = (F_perm * (1.0 - 0.05) * B + F_bleed * B) / V_reactor
        loss_D = (F_perm * (1.0 - R_prod) * D + F_bleed * D) / V_reactor
        loss_L = (F_perm * (1.0 - R_prod) * L + F_bleed * L) / V_reactor
        
        dA = (F_in * A_feed) / V_reactor - loss_A - r_rac - r_cat_D - r_cat_L
        dB = (F_in * B_feed) / V_reactor - loss_B - r_rac - r_cat_D - r_cat_L
        dD = 0.5 * r_rac + r_cat_D - loss_D
        dL = 0.5 * r_rac + r_cat_L - loss_L
        dND = F_bleed * D
        
        return [dA, dB, dD, dL, dND]
    return ode

# --- 3. FULL-RANGE PARAMETER SWEEP UP TO 25 m/s & TOTAL PRESSURE CALCULATION ---
print("Scanning v_loop velocity range from 0.05 to 25.0 m/s...")
v_sweep = np.linspace(0.05, 25.0, 60)
ee_end = []
yield_end = []
friction_dp_bar = []
total_dp_bar = []

t_eval_sweep = (0, 43200) # Evaluation after 12 hours
y0 = [0.0, 0.0, 1e-6, 1e-6, 0.0]

for v in v_sweep:
    sol_v = solve_ivp(make_system_ode(v), t_eval_sweep, y0, method='Radau')
    D_f = sol_v.y[2][-1]
    L_f = sol_v.y[3][-1]
    tot = D_f + L_f
    ee_val = (abs(D_f - L_f) / tot * 100.0) if tot > 1e-6 else 0.0
    ee_end.append(ee_val)
    yield_end.append(sol_v.y[4][-1])
    
    # 1. Friction pressure drop (bar)
    p_fric = calc_friction_dp(v) / 1e5
    friction_dp_bar.append(p_fric)
    
    # 2. Partial osmotic pressure (bar) across OSN membrane
    # Transmembrane concentration difference: Delta_C = R_prod * [D + L]
    delta_C = R_prod * tot
    pi_osmotic = calc_osmotic_pressure(delta_C) / 1e5
    
    # 3. Total membrane pressure: Delta_P_total = Delta_P_friction + Delta_pi
    p_tot = p_fric + pi_osmotic
    total_dp_bar.append(p_tot)

ee_end = np.array(ee_end)
friction_dp_bar = np.array(friction_dp_bar)
total_dp_bar = np.array(total_dp_bar)

# Determine safe operating boundaries
idx_safe = np.where(ee_end >= 95.0)[0]
v_min_safe = v_sweep[idx_safe[0]] if len(idx_safe) > 0 else np.nan

# Former mechanical limit (pure friction only)
idx_burst_fric = np.where(friction_dp_bar >= 30.0)[0]
v_max_fric_only = v_sweep[idx_burst_fric[0]] if len(idx_burst_fric) > 0 else 25.0

# Realistic mechanical limit (cumulative osmotic pressure)
idx_burst_total = np.where(total_dp_bar >= 30.0)[0]
v_max_real = v_sweep[idx_burst_total[0]] if len(idx_burst_total) > 0 else np.nan

# ==============================================================================
# COMPLETE PLOTTING
# ==============================================================================
plt.figure(figsize=(14, 6))
ax = plt.subplot(1, 1, 1)
ax_twin = ax.twinx()

# %ee Curve
line_ee = ax.plot(v_sweep, ee_end, 'b-', linewidth=2.5, label='Optical Purity (%ee after 12h)')
ax.axhline(95.0, color='blue', linestyle=':', label='Required Threshold $ee = 95\%$')
ax.set_xlabel('Recirculation Loop Velocity $v_{loop}$ (m/s)', fontsize=12)
ax.set_ylabel('Enantiomeric Excess (%)', color='b', fontsize=12)
ax.tick_params(axis='y', labelcolor='b')
ax.set_ylim([50, 101])
ax.set_xlim([0, 25.0])

# Pressure Curves
line_p_fric = ax_twin.plot(v_sweep, friction_dp_bar, 'orange', linestyle='--', linewidth=2, 
                           label=r'Hydraulic Friction Pressure Drop $\Delta P_{friction}$')
line_p_tot = ax_twin.plot(v_sweep, total_dp_bar, 'r-', linewidth=2.5, 
                          label=r'Total Membrane Pressure: $\Delta P_{total} = \Delta P_{friction} + \Delta \pi$')
ax_twin.axhline(30.0, color='darkred', linestyle='-.', linewidth=2.5, label='OSN Membrane Burst Pressure Limit (30 bar)')
ax_twin.set_ylabel('Effective Pressure (bar)', color='darkred', fontsize=12)
ax_twin.tick_params(axis='y', labelcolor='darkred')
ax_twin.set_ylim([0, 50])

# Highlight realistic feasible window
ax.axvspan(v_min_safe, v_max_real, color='green', alpha=0.18, 
           label=f'Realistic Safe Window: [{v_min_safe:.2f} m/s $\rightarrow$ {v_max_real:.2f} m/s]')

# Velocity limit points
ax.axvline(v_min_safe, color='green', linestyle='--', linewidth=2)
ax.axvline(v_max_real, color='darkred', linestyle='--', linewidth=2)
ax.axvline(v_max_fric_only, color='gray', linestyle=':', linewidth=1.5, alpha=0.7)

ax.set_title(r'Hydraulic - Osmotic Optimization: Operating Window Accounting for Osmotic Pressure $\Delta \pi$', fontsize=13)
ax.grid(True, linestyle='--', alpha=0.6)

# Combine legends from both axes
lines = line_ee + [ax.get_lines()[1]] + line_p_fric + line_p_tot + [ax_twin.get_lines()[2]]
labels = [l.get_label() for l in lines]
ax.legend(lines, labels, loc='center right', framealpha=0.9)

plt.tight_layout()
plt.show()
