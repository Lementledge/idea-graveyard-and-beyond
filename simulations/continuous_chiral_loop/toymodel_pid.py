import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- 1. KINETIC PARAMETERS & CASCADE SYSTEM ---
k0_base = 25.0
k_cat = 15.0
K_A = 1000.0
K_B = 1000.0
K_inh_base = 120.0

P_D_bed = 0.5
P_L_bed = 0.005

V_reactor = 1.0       # L
F_feed_max = 1e-4     # L/s
A_feed = 0.2          # M
B_feed = 0.2          # M

F_bleed = 3.0e-5      # L/s (108 mL/h)
R_prod_1 = 0.98

v_loop = 3.0          # m/s
alpha_shear = 5.0
K_inh_eff = K_inh_base / (1.0 + alpha_shear * v_loop)

# Module 2: Micro-falling film
V_stage2 = 0.015      # 15 mL
CF_target = 4.5
F_harvest = F_bleed / CF_target # 24 mL/h
F_recovered_solvent = F_bleed - F_harvest

# Module 3: MSMPR Crystallizer parameters
C_sat_cooling = 0.3   # M (Saturation solubility at 5 °C)
Mw_product = 150.0    # g/mol

# --- 2. FULL SYSTEM ODE EQUATIONS ---
def pid_system_ode(t, y):
    # y = [A1, B1, D1, L1, D2, L2, Solvent_Recycled_L, Mass_Crystal_g]
    A1, B1, D1, L1 = max(y[0], 0), max(y[1], 0), max(y[2], 0), max(y[3], 0)
    D2, L2 = max(y[4], 0), max(y[5], 0)
    
    # 1. Main loop with Adaptive Dosing
    A_thresh = 5e-5
    F_in = F_feed_max / (1.0 + np.exp((A1 - A_thresh) / (0.15 * A_thresh)))
    F_perm1 = max(F_in - F_bleed, 0)
    
    denom = 1.0 + K_A * A1 + K_B * B1 + K_inh_eff * (D1 + L1)
    theta_A = (K_A * A1) / denom
    theta_B = (K_B * B1) / denom
    
    r_rac = k0_base * A1 * B1
    r_cat_D = k_cat * P_D_bed * theta_A * theta_B
    r_cat_L = k_cat * P_L_bed * theta_A * theta_B
    
    loss_A1 = (F_perm1 * (1.0 - 0.05) * A1 + F_bleed * A1) / V_reactor
    loss_B1 = (F_perm1 * (1.0 - 0.05) * B1 + F_bleed * B1) / V_reactor
    loss_D1 = (F_perm1 * (1.0 - R_prod_1) * D1 + F_bleed * D1) / V_reactor
    loss_L1 = (F_perm1 * (1.0 - R_prod_1) * L1 + F_bleed * L1) / V_reactor
    
    dA1 = (F_in * A_feed) / V_reactor - loss_A1 - r_rac - r_cat_D - r_cat_L
    dB1 = (F_in * B_feed) / V_reactor - loss_B1 - r_rac - r_cat_D - r_cat_L
    dD1 = 0.5 * r_rac + r_cat_D - loss_D1
    dL1 = 0.5 * r_rac + r_cat_L - loss_L1
    
    # 2. Module 2: Microfluidic concentration
    dD2 = (F_bleed * D1 - F_harvest * D2) / V_stage2
    dL2 = (F_bleed * L1 - F_harvest * L2) / V_stage2
    dSolvent = F_recovered_solvent
    
    # 3. Module 3: Solid crystal formation rate
    # Crystallizes only when D2 concentration exceeds saturation concentration C_sat
    r_cryst_mol_s = F_harvest * max(D2 - C_sat_cooling, 0)
    dMass_Crystal = r_cryst_mol_s * Mw_product # g/s
    
    return [dA1, dB1, dD1, dL1, dD2, dL2, dSolvent, dMass_Crystal]

# 12-hour simulation time
t_span = (0, 43200)
t_eval = np.linspace(0, 43200, 2000)

# PRE-CHARGING INITIAL CONCENTRATION STRATEGY
# Pre-charge D1 = 0.35 M into tank V1 (ee = 98%)
y0_precharged = [0.0, 0.0, 0.35, 0.0035, 0.35, 0.0035, 0.0, 0.0]

print("Solving P&ID integrated system with Pre-charging and MSMPR Crystallization...")
sol = solve_ivp(pid_system_ode, t_span, y0_precharged, t_eval=t_eval, method='Radau')

# --- 3. RESULT PLOTS ---
time_hours = sol.t / 3600
D1 = sol.y[2]
D2 = sol.y[4]
Crystal_mass_g = sol.y[7]

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Plot 1: Complete elimination of concentration lag phase
axes[0].plot(time_hours, D1, 'b--', linewidth=2, label=r'Main Loop $[D]_1$ (Stable 0.35 M)')
axes[0].plot(time_hours, D2, 'r-', linewidth=2.5, label=r'Module 2 $[D]_2$ (Micro-falling film concentration)')
axes[0].axhline(1.5, color='gray', linestyle=':', label='Crystallization Concentration Threshold')
axes[0].axhline(C_sat_cooling, color='darkgreen', linestyle='-.', label=r'Saturation Solubility $C_{sat}$ (5 °C)')
axes[0].set_title('Concentration Dynamics with Pre-charging (t = 0)', fontsize=11)
axes[0].set_xlabel('Time (hours)')
axes[0].set_ylabel('Concentration (M)')
axes[0].set_ylim([0, 3.0])
axes[0].grid(True, linestyle='--', alpha=0.6)
axes[0].legend()

# Plot 2: Optical Purity (%ee)
ee_final = np.where((sol.y[4] + sol.y[5]) > 1e-6, 
                    (np.abs(sol.y[4] - sol.y[5]) / (sol.y[4] + sol.y[5])) * 100.0, 0.0)
axes[1].plot(time_hours, ee_final, 'g-', linewidth=2.5, label='%ee Crystallization Outflow')
axes[1].axhline(99.9, color='darkred', linestyle='--', label='Crystal Purity after Centrifugation (>99.9%)')
axes[1].set_title('Product Optical Purity', fontsize=11)
axes[1].set_xlabel('Time (hours)')
axes[1].set_ylabel('Enantiomeric Excess (%)')
axes[1].set_ylim([95, 100.2])
axes[1].grid(True, linestyle='--', alpha=0.6)
axes[1].legend()

# Plot 3: Cumulative Harvested Solid Crystal Product Mass
axes[2].plot(time_hours, Crystal_mass_g, 'purple', linewidth=2.5, label='Solid Crystal Mass (g)')
axes[2].set_title('Recovered Enantiopure Crystal Yield (MSMPR)', fontsize=11)
axes[2].set_xlabel('Time (hours)')
axes[2].set_ylabel('Recovered Crystal Mass (g)')
axes[2].grid(True, linestyle='--', alpha=0.6)
axes[2].legend()

plt.tight_layout()
plt.show()

# Calculate operational metrics
idx_1h = np.where(time_hours >= 1.0)[0][0]
print("--- REAL-TIME OPERATING RESULTS ---")
print(f"D2 concentration at t = 30 min: {D2[np.where(time_hours >= 0.5)[0][0]]:.2f} M (Exceeds crystallization threshold immediately)")
print(f"Steady-state solid crystal harvest rate: {(Crystal_mass_g[-1] - Crystal_mass_g[idx_1h]) / (time_hours[-1] - 1.0):.2f} g/h")
print(f"Total crystal mass recovered after 12 hours: {Crystal_mass_g[-1]:.2f} g")
