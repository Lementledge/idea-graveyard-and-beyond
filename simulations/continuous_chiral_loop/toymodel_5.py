import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- 1. KINETIC PARAMETERS & CONFIGURATION OF LOOP 1 (MAIN REACTION LOOP) ---
k0_base = 25.0        # L/(mol*s)
k_cat = 15.0          # 1/s
K_A = 1000.0          # L/mol
K_B = 1000.0          # L/mol
K_inh_base = 120.0    # L/mol

P_D_bed = 0.5         # mol/L
P_L_bed = 0.005       # ee_bed = 98%

V_reactor = 1.0       # L (Isochoric due to total solvent recycling)
F_feed_max = 1e-4     # L/s (0.1 mL/s)
A_feed = 0.2          # M
B_feed = 0.2          # M

F_bleed = 3.0e-5      # L/s (0.108 L/h) transferred to module 2
R_prod_1 = 0.98       # Main loop OSN membrane

# Select optimal safe operating velocity from previous plot: v = 3.0 m/s
v_loop = 3.0          # m/s
alpha_shear = 5.0     # s/m
K_inh_eff = K_inh_base / (1.0 + alpha_shear * v_loop)

# Thermodynamic constants for osmotic pressure calculation
R_gas = 8.314         # J/(mol*K)
Temp_K = 298.15       # 25 °C

def calc_osmotic_pressure(conc_diff_M):
    return (conc_diff_M * 1000.0) * R_gas * Temp_K

# --- 2. SECONDARY MODULE PARAMETERS (STAGE 2 CONCENTRATOR) ---
V_stage2 = 0.2        # Secondary concentration chamber volume (L)
# Outlet concentration target for crystallization: 1.5 M
# Secondary evaporation/solvent separation rate automatically regulated by concentration
Delta_H_vap = 40.0    # kJ/mol (~ organic solvents such as MeOH, MeCN, THF)
rho_solvent = 800.0   # g/L
M_solvent = 60.0      # g/mol -> solvent molar concentration ~ 13.3 mol/L

# --- 3. TWO-STAGE COUPLED SYSTEM ODE EQUATIONS ---
def two_stage_system_ode(t, y):
    # y = [A1, B1, D1, L1, D2, L2, Solvent_Recycled_L]
    A1, B1, D1, L1 = max(y[0], 0), max(y[1], 0), max(y[2], 0), max(y[3], 0)
    D2, L2 = max(y[4], 0), max(y[5], 0)
    
    # ------------------ STAGE 1: MAIN LOOP ------------------
    A_thresh = 5e-5
    F_in = F_feed_max / (1.0 + np.exp((A1 - A_thresh) / (0.15 * A_thresh)))
    F_perm1 = max(F_in - F_bleed, 0)
    
    denom = 1.0 + K_A * A1 + K_B * B1 + K_inh_eff * (D1 + L1)
    theta_A = (K_A * A1) / denom
    theta_B = (K_B * B1) / denom
    
    r_rac = k0_base * A1 * B1
    r_cat_D = k_cat * P_D_bed * theta_A * theta_B
    r_cat_L = k_cat * P_L_bed * theta_A * theta_B
    
    # Loss via stage 1 membrane permeate + bleed stream to stage 2
    loss_A1 = (F_perm1 * (1.0 - 0.05) * A1 + F_bleed * A1) / V_reactor
    loss_B1 = (F_perm1 * (1.0 - 0.05) * B1 + F_bleed * B1) / V_reactor
    loss_D1 = (F_perm1 * (1.0 - R_prod_1) * D1 + F_bleed * D1) / V_reactor
    loss_L1 = (F_perm1 * (1.0 - R_prod_1) * L1 + F_bleed * L1) / V_reactor
    
    dA1 = (F_in * A_feed) / V_reactor - loss_A1 - r_rac - r_cat_D - r_cat_L
    dB1 = (F_in * B_feed) / V_reactor - loss_B1 - r_rac - r_cat_D - r_cat_L
    dD1 = 0.5 * r_rac + r_cat_D - loss_D1
    dL1 = 0.5 * r_rac + r_cat_L - loss_L1
    
    # ------------------ STAGE 2: DECOUPLED CONCENTRATOR ------------------
    # Final purified product withdrawal stream from system (Harvest stream)
    # Withdrawn at a lower flow rate than F_bleed to concentrate: CF = 4.5 -> F_harvest = F_bleed / 4.5
    CF_target = 4.5
    F_harvest = F_bleed / CF_target
    
    # Flow rate of evaporated/membrane-separated solvent to recover:
    F_recovered_solvent = F_bleed - F_harvest # L/s
    
    # Concentration balance in stage 2 concentrator
    dD2 = (F_bleed * D1 - F_harvest * D2) / V_stage2
    dL2 = (F_bleed * L1 - F_harvest * L2) / V_stage2
    
    # Cumulative total of pure recovered/recycled solvent
    dSolvent = F_recovered_solvent
    
    return [dA1, dB1, dD1, dL1, dD2, dL2, dSolvent]

# Run 24-hour simulation
t_span = (0, 86400)
t_eval = np.linspace(0, 86400, 2000)
y0 = [0.0, 0.0, 1e-6, 1e-6, 1e-6, 1e-6, 0.0]

print("Solving 2-stage coupled system (Main Loop + Secondary Concentrator)...")
sol = solve_ivp(two_stage_system_ode, t_span, y0, t_eval=t_eval, method='Radau')

# --- 4. TECHNICAL METRICS CALCULATION ---
time_hours = sol.t / 3600
D1 = sol.y[2]
L1 = sol.y[3]
D2 = sol.y[4]
L2 = sol.y[5]

ee_stage1 = np.where((D1 + L1) > 1e-6, (np.abs(D1 - L1) / (D1 + L1)) * 100.0, 0.0)
ee_stage2 = np.where((D2 + L2) > 1e-6, (np.abs(D2 - L2) / (D2 + L2)) * 100.0, 0.0)

# Solvent separation load and required thermal power for secondary module
CF = 4.5
F_solvent_rec_L_h = (F_bleed - (F_bleed / CF)) * 3600 # L/h
mol_solvent_per_s = (F_bleed - (F_bleed / CF)) * (rho_solvent / M_solvent)
Power_kW = mol_solvent_per_s * Delta_H_vap # Evaporative thermal power (kW)

# --- 5. VISUALIZATION OF RESULTS ---
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Plot 1: Two-stage concentration evolution
axes[0].plot(time_hours, D1, 'b--', linewidth=2, label=r'Main Loop $[D]_1$ (Suppressed to reduce $\Delta\pi$)')
axes[0].plot(time_hours, D2, 'r-', linewidth=2.5, label='Module 2 $[D]_2$ (Concentrated for crystallization)')
axes[0].axhline(1.5, color='darkred', linestyle=':', label='Crystallization Target ($1.5$ M)')
axes[0].set_title('Product Concentration Across Two Stages', fontsize=11)
axes[0].set_xlabel('Operating Time (hours)')
axes[0].set_ylabel('Product Concentration [D] (M)')
axes[0].grid(True, linestyle='--', alpha=0.6)
axes[0].legend()

# Plot 2: Conservation of optical purity (%ee)
axes[1].plot(time_hours, ee_stage1, 'b--', linewidth=2, label='%ee Main Loop')
axes[1].plot(time_hours, ee_stage2, 'g-', linewidth=2, label='%ee Post-concentration Product')
axes[1].axhline(95.0, color='gray', linestyle=':', label='Required Threshold $95\%$')
axes[1].set_title('Enantiomeric Excess Across Two Stages', fontsize=11)
axes[1].set_xlabel('Operating Time (hours)')
axes[1].set_ylabel('Enantiomeric Excess (%)')
axes[1].set_ylim([90, 100])
axes[1].grid(True, linestyle='--', alpha=0.6)
axes[1].legend()

# Plot 3: Solvent balance & Secondary separation power
ax3_twin = axes[2].twinx()
axes[2].plot(time_hours, sol.y[6], 'purple', linewidth=2, label='Cumulative Recovered Solvent (L)')
ax3_twin.plot(time_hours, np.full_like(time_hours, Power_kW * 1000), 'orange', linestyle='--', 
              linewidth=2, label='Evaporative Thermal Power (W)')

axes[2].set_title('Recycled Solvent Load & Secondary Thermal Power', fontsize=11)
axes[2].set_xlabel('Operating Time (hours)')
axes[2].set_ylabel('Recycled Solvent Volume (L)', color='purple')
axes[2].tick_params(axis='y', labelcolor='purple')
ax3_twin.set_ylabel('Evaporative Thermal Power (W)', color='darkorange')
ax3_twin.tick_params(axis='y', labelcolor='darkorange')
ax3_twin.set_ylim([0, 100])
axes[2].grid(True, linestyle='--', alpha=0.6)

# Combine legends for plot 3
lines3 = axes[2].get_lines() + ax3_twin.get_lines()
labels3 = [l.get_label() for l in lines3]
axes[2].legend(lines3, labels3, loc='center left')

plt.tight_layout()
plt.show()

print("--- STEADY-STATE OPERATING PARAMETERS ---")
print(f"Main loop concentration [D]1: {D1[-1]:.2f} M (Osmotic pressure: {calc_osmotic_pressure(0.98 * D1[-1])/1e5:.1f} bar)")
print(f"Post-concentration concentration [D]2: {D2[-1]:.2f} M (Ready for crystallization)")
print(f"Solvent recovery flow rate required: {F_solvent_rec_L_h:.3f} L/h (~{F_solvent_rec_L_h*1000/60:.1f} mL/min)")
print(f"Required thin-film evaporation heating power: {Power_kW * 1000:.1f} W")
