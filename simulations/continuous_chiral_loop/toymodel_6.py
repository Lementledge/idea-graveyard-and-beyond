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

v_loop = 3.0          # m/s (well within expanded safe window)
alpha_shear = 5.0     # s/m
K_inh_eff = K_inh_base / (1.0 + alpha_shear * v_loop)

# --- 2. SECONDARY MODULE PARAMETERS (MICRO-FALLING FILM CONCENTRATOR) ---
# Optimization: Reduced holdup volume from 200 mL to 15 mL
V_stage2 = 0.015      # 15 mL hold-up volume

Delta_H_vap = 40.0    # kJ/mol
rho_solvent = 800.0   # g/L
M_solvent = 60.0      # g/mol

# --- 3. TWO-STAGE COUPLED ODE EQUATIONS ---
def two_stage_system_ode(t, y):
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
    
    loss_A1 = (F_perm1 * (1.0 - 0.05) * A1 + F_bleed * A1) / V_reactor
    loss_B1 = (F_perm1 * (1.0 - 0.05) * B1 + F_bleed * B1) / V_reactor
    loss_D1 = (F_perm1 * (1.0 - R_prod_1) * D1 + F_bleed * D1) / V_reactor
    loss_L1 = (F_perm1 * (1.0 - R_prod_1) * L1 + F_bleed * L1) / V_reactor
    
    dA1 = (F_in * A_feed) / V_reactor - loss_A1 - r_rac - r_cat_D - r_cat_L
    dB1 = (F_in * B_feed) / V_reactor - loss_B1 - r_rac - r_cat_D - r_cat_L
    dD1 = 0.5 * r_rac + r_cat_D - loss_D1
    dL1 = 0.5 * r_rac + r_cat_L - loss_L1
    
    # ------------------ STAGE 2: MICRO-FALLING FILM ------------------
    CF_target = 4.5
    F_harvest = F_bleed / CF_target
    F_recovered_solvent = F_bleed - F_harvest
    
    # Balance with micro-volume V_stage2 = 15 mL
    dD2 = (F_bleed * D1 - F_harvest * D2) / V_stage2
    dL2 = (F_bleed * L1 - F_harvest * L2) / V_stage2
    dSolvent = F_recovered_solvent
    
    return [dA1, dB1, dD1, dL1, dD2, dL2, dSolvent]

# Run 24-hour simulation
t_span = (0, 86400)
t_eval = np.linspace(0, 86400, 2000)
y0 = [0.0, 0.0, 1e-6, 1e-6, 1e-6, 1e-6, 0.0]

print("Solving system with micro-volume concentration chamber (V_stage2 = 15 mL)...")
sol = solve_ivp(two_stage_system_ode, t_span, y0, t_eval=t_eval, method='Radau')

# --- 4. TECHNICAL METRICS CALCULATION ---
time_hours = sol.t / 3600
D1 = sol.y[2]
L1 = sol.y[3]
D2 = sol.y[4]
L2 = sol.y[5]

ee_stage1 = np.where((D1 + L1) > 1e-6, (np.abs(D1 - L1) / (D1 + L1)) * 100.0, 0.0)
ee_stage2 = np.where((D2 + L2) > 1e-6, (np.abs(D2 - L2) / (D2 + L2)) * 100.0, 0.0)

CF = 4.5
F_solvent_rec_L_h = (F_bleed - (F_bleed / CF)) * 3600
mol_solvent_per_s = (F_bleed - (F_bleed / CF)) * (rho_solvent / M_solvent)
Power_kW = mol_solvent_per_s * Delta_H_vap

# Find onset time reaching 1.5 M crystallization threshold
idx_crystallize = np.where(D2 >= 1.5)[0]
t_crystallize_hr = time_hours[idx_crystallize[0]] if len(idx_crystallize) > 0 else np.nan

# --- 5. VISUALIZATION OF RESULTS ---
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Plot 1: Concentration evolution with ultra-low latency
axes[0].plot(time_hours, D1, 'b--', linewidth=2, label=r'Main Loop $[D]_1$ ($\sim 0.35$ M)')
axes[0].plot(time_hours, D2, 'r-', linewidth=2.5, label=r'Micro-film $[D]_2$ ($V_{hold} = 15$ mL)')
axes[0].axhline(1.5, color='darkred', linestyle=':', label='Crystallization Threshold ($1.5$ M)')
if not np.isnan(t_crystallize_hr):
    axes[0].axvline(t_crystallize_hr, color='green', linestyle='--', 
                    label=f'Harvest Onset ({t_crystallize_hr:.1f} h)')

axes[0].set_title('Product Concentration: Ultra-fast Response of Micro-Concentrator', fontsize=11)
axes[0].set_xlabel('Operating Time (hours)')
axes[0].set_ylabel('Product Concentration [D] (M)')
axes[0].set_xlim([0, 24])
axes[0].grid(True, linestyle='--', alpha=0.6)
axes[0].legend()

# Plot 2: %ee Conservation
axes[1].plot(time_hours, ee_stage1, 'b--', linewidth=2, label='%ee Main Loop')
axes[1].plot(time_hours, ee_stage2, 'g-', linewidth=2, label='%ee Post-concentration')
axes[1].axhline(95.0, color='gray', linestyle=':', label='Required Threshold $95\%$')
axes[1].set_title('Optical Purity (%ee)', fontsize=11)
axes[1].set_xlabel('Operating Time (hours)')
axes[1].set_ylabel('Enantiomeric Excess (%)')
axes[1].set_ylim([90, 100])
axes[1].grid(True, linestyle='--', alpha=0.6)
axes[1].legend()

# Plot 3: Solvent Recycling & Thermal Power
ax3_twin = axes[2].twinx()
axes[2].plot(time_hours, sol.y[6], 'purple', linewidth=2, label='Recycled Solvent (L)')
ax3_twin.plot(time_hours, np.full_like(time_hours, Power_kW * 1000), 'orange', linestyle='--', 
              linewidth=2, label='Evaporation Thermal Power (W)')

axes[2].set_title('Recycled Solvent Load & Secondary Power', fontsize=11)
axes[2].set_xlabel('Operating Time (hours)')
axes[2].set_ylabel('Solvent Volume (L)', color='purple')
ax3_twin.set_ylabel('Power (Watts)', color='darkorange')
ax3_twin.set_ylim([0, 100])
axes[2].grid(True, linestyle='--', alpha=0.6)

lines3 = axes[2].get_lines() + ax3_twin.get_lines()
labels3 = [l.get_label() for l in lines3]
axes[2].legend(lines3, labels3, loc='center left')

plt.tight_layout()
plt.show()

print(f"Time to reach 1.5 M crystallization threshold: {t_crystallize_hr:.2f} hours")
print(f"Steady-state concentration at crystallizer inlet: {D2[-1]:.2f} M")
