import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- 1. KINETIC PARAMETERS & PRESSURE MITIGATION CONFIGURATION ---
k0_base = 25.0        # L/(mol*s)
k_cat = 15.0          # 1/s
K_A = 1000.0          # L/mol
K_B = 1000.0          # L/mol
K_inh_base = 120.0    # L/mol

P_D_bed = 0.5         # mol/L
P_L_bed = 0.005       # ee_bed = 98%

V_reactor = 1.0       # L
F_feed_max = 1e-4     # L/s (0.1 mL/s)

# STRATEGY 1 & 3: INCREASE F_BLEED AND LOWER FEED CONCENTRATION
F_bleed = 3.0e-5      # Increased from 1e-5 to 3e-5 L/s (30% of F_feed)
A_feed = 0.2          # Reduced from 0.5 M to 0.2 M
B_feed = 0.2          # Reduced from 0.5 M to 0.2 M
R_prod = 0.98         # OSN membrane

# Hydraulic & thermodynamic constants
mu_solvent = 1.0e-3   # Pa*s
channel_L = 1.0       # m
d_hydraulic = 5e-4    # m (500 micrometers)
P_max_membrane = 30e5 # 30 bar = 3e6 Pa
alpha_shear = 5.0     # s/m

R_gas = 8.314         # J/(mol*K)
Temp_K = 298.15       # 25 °C

def calc_friction_dp(v):
    return (32.0 * mu_solvent * channel_L / (d_hydraulic**2)) * v

def calc_osmotic_pressure(conc_diff_M):
    return (conc_diff_M * 1000.0) * R_gas * Temp_K

# --- 2. SYSTEM ODE EQUATIONS ---
def make_system_ode(v_loop):
    K_inh_eff = K_inh_base / (1.0 + alpha_shear * v_loop)
    
    def ode(t, y):
        A, B, D, L = max(y[0], 0), max(y[1], 0), max(y[2], 0), max(y[3], 0)
        
        # Adaptive Dosing Controller (5e-5 M threshold)
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

# --- 3. FULL VELOCITY SWEEP ---
print("Scanning v_loop velocity range to inspect expanded safe window...")
v_sweep = np.linspace(0.05, 25.0, 60)
ee_end = []
yield_end = []
friction_dp_bar = []
total_dp_bar = []
conc_D_end = []

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
    conc_D_end.append(tot)
    
    # Hydraulic friction pressure drop
    p_fric = calc_friction_dp(v) / 1e5
    friction_dp_bar.append(p_fric)
    
    # Osmotic pressure with suppressed concentration
    delta_C = R_prod * tot
    pi_osmotic = calc_osmotic_pressure(delta_C) / 1e5
    
    # Total pressure
    total_dp_bar.append(p_fric + pi_osmotic)

ee_end = np.array(ee_end)
friction_dp_bar = np.array(friction_dp_bar)
total_dp_bar = np.array(total_dp_bar)
conc_D_end = np.array(conc_D_end)

# Determine boundaries of expanded safe window
idx_safe = np.where(ee_end >= 95.0)[0]
v_min_safe = v_sweep[idx_safe[0]] if len(idx_safe) > 0 else np.nan

idx_burst_total = np.where(total_dp_bar >= 30.0)[0]
v_max_real = v_sweep[idx_burst_total[0]] if len(idx_burst_total) > 0 else 25.0

# --- 4. VISUALIZATION ---
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

# Expanded safe window
ax.axvspan(v_min_safe, v_max_real, color='green', alpha=0.18, 
           label=f'Expanded Safe Window: [{v_min_safe:.2f} m/s $\rightarrow$ {v_max_real:.2f} m/s]')

ax.axvline(v_min_safe, color='green', linestyle='--', linewidth=2)
ax.axvline(v_max_real, color='darkred', linestyle='--', linewidth=2)

ax.set_title(r'Expanded Safe Window by Suppressing $[D] \approx 0.3 - 0.4\text{ M}$ (Reducing $\Delta \pi$)', fontsize=13)
ax.grid(True, linestyle='--', alpha=0.6)

lines = line_ee + [ax.get_lines()[1]] + line_p_fric + line_p_tot + [ax_twin.get_lines()[2]]
labels = [l.get_label() for l in lines]
ax.legend(lines, labels, loc='center right', framealpha=0.9)

plt.tight_layout()
plt.show()

print(f"Steady-state product concentration in tank: ~{conc_D_end[int(idx_safe[0])]:.2f} M")
print(f"Partial osmotic pressure Delta_pi: ~{calc_osmotic_pressure(0.98 * conc_D_end[int(idx_safe[0])]) / 1e5:.1f} bar")
print(f"New feasible velocity window: [{v_min_safe:.2f} m/s --> {v_max_real:.2f} m/s]")
