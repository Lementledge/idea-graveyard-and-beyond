import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# ==============================================================================
# PARTS 1, 3 & 4: 24-HOUR SIMULATION WITH ADAPTIVE DOSING & DESORPTION BOOST
# ==============================================================================

# Base kinetic parameters
k0_base = 10.0         # Background racemic reaction (L/(mol*s))
k_cat = 15.0          # Maximum turnover frequency on chiral bed (1/s)
K_A = 1000.0          # Adsorption affinity of A (L/mol)
K_B = 1000.0          # Adsorption affinity of B (L/mol)
K_inh_base = 50.0     # Base binding affinity of product (L/mol)

P_D_bed = 0.5         # Template D density (mol/L)
P_L_bed = 0.005       # Impurity L (bed ee = 98%)

V_reactor = 1.0       # Reaction loop volume (L)
F_feed_max = 1e-4     # Maximum feed flow rate (0.1 mL/s)
A_feed = 0.5          # Syringe concentration (M)
B_feed = 0.5
R_prod = 0.98         # Product rejection coefficient (OSN membrane)
F_bleed = 1e-5        # Concentrated product bleed flow rate (L/s)

# Desorption Boost parameters: Flushing flow / shear stress & thermal gradient effects
# K_inh_eff = K_inh_base / (1 + gamma_shear * v_flow + beta_temp * delta_T)
boost_factor = 2.5    # 2.5x reduction in re-binding affinity via shear force and thermal pulse
K_inh_eff = K_inh_base / boost_factor

# Kinetic function with Adaptive Dosing controller
def osn_system_ode(t, y, adaptive=True):
    A, B, D, L = max(y[0], 0), max(y[1], 0), max(y[2], 0), max(y[3], 0)
    
    # 1. Adaptive Dosing controller: Throttles F_feed when [A] exceeds 5e-5 M threshold
    A_threshold = 5e-5
    if adaptive:
        # Sigmoid function smoothly modulates feed flow rate to protect ultra-dilute condition
        F_in = F_feed_max / (1.0 + np.exp((A - A_threshold) / (0.15 * A_threshold)))
    else:
        F_in = F_feed_max
        
    F_perm = max(F_in - F_bleed, 0)
    
    # 2. Competitive Langmuir adsorption with Desorption Boost
    denom = 1.0 + K_A * A + K_B * B + K_inh_eff * (D + L)
    theta_A = (K_A * A) / denom
    theta_B = (K_B * B) / denom
    
    # 3. Reaction rates
    r_rac = k0_base * A * B
    r_cat_D = k_cat * P_D_bed * theta_A * theta_B
    r_cat_L = k_cat * P_L_bed * theta_A * theta_B
    
    # 4. Material balances (OSN loop)
    loss_A = (F_perm * (1.0 - 0.05) * A + F_bleed * A) / V_reactor
    loss_B = (F_perm * (1.0 - 0.05) * B + F_bleed * B) / V_reactor
    loss_D = (F_perm * (1.0 - R_prod) * D + F_bleed * D) / V_reactor
    loss_L = (F_perm * (1.0 - R_prod) * L + F_bleed * L) / V_reactor
    
    dA = (F_in * A_feed) / V_reactor - loss_A - r_rac - r_cat_D - r_cat_L
    dB = (F_in * B_feed) / V_reactor - loss_B - r_rac - r_cat_D - r_cat_L
    dD = 0.5 * r_rac + r_cat_D - loss_D
    dL = 0.5 * r_rac + r_cat_L - loss_L
    
    return [dA, dB, dD, dL]

# Run 24-hour simulation
t_span_24h = (0, 86400) # 24 hours
t_eval_24h = np.linspace(0, 86400, 3000)
y0 = [0.0, 0.0, 1e-6, 1e-6]

# Scenario 1: Without adaptive control (Fixed Dosing)
sol_fixed = solve_ivp(lambda t, y: osn_system_ode(t, y, adaptive=False),
                      t_span_24h, y0, t_eval=t_eval_24h, method='Radau')

# Scenario 2: With adaptive control (Adaptive Dosing + Desorption Boost)
sol_adapt = solve_ivp(lambda t, y: osn_system_ode(t, y, adaptive=True),
                      t_span_24h, y0, t_eval=t_eval_24h, method='Radau')

def calc_ee_array(sol):
    diff = np.abs(sol.y[2] - sol.y[3])
    tot = sol.y[2] + sol.y[3]
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(tot > 1e-7, (diff / tot) * 100.0, 0.0)

ee_fixed = calc_ee_array(sol_fixed)
ee_adapt = calc_ee_array(sol_adapt)

# ==============================================================================
# PART 2: HEATMAP SCAN TO FIND THE "SAFE OPERATING WINDOW"
# ==============================================================================
print("Scanning parameter space (K_inh x k0)...")
grid_res = 25
k0_range = np.linspace(1.0, 100.0, grid_res)
K_inh_range = np.linspace(0.0, 200.0, grid_res)
ee_grid = np.zeros((grid_res, grid_res))

# Evaluate %ee at 12-hour stopping point
t_eval_sweep = (0, 43200)

for i, k0_val in enumerate(k0_range):
    for j, Kinh_val in enumerate(K_inh_range):
        def sweep_ode(t, y):
            A, B, D, L = max(y[0], 0), max(y[1], 0), max(y[2], 0), max(y[3], 0)
            denom = 1.0 + K_A * A + K_B * B + Kinh_val * (D + L)
            theta_A = (K_A * A) / denom
            theta_B = (K_B * B) / denom
            
            r_rac = k0_val * A * B
            r_cat_D = k_cat * P_D_bed * theta_A * theta_B
            r_cat_L = k_cat * P_L_bed * theta_A * theta_B
            
            F_perm = F_feed_max - F_bleed
            loss_D = (F_perm * (1.0 - R_prod) * D + F_bleed * D) / V_reactor
            loss_L = (F_perm * (1.0 - R_prod) * L + F_bleed * L) / V_reactor
            
            dA = (F_feed_max * A_feed) / V_reactor - r_rac - r_cat_D - r_cat_L
            dB = (F_feed_max * B_feed) / V_reactor - r_rac - r_cat_D - r_cat_L
            dD = 0.5 * r_rac + r_cat_D - loss_D
            dL = 0.5 * r_rac + r_cat_L - loss_L
            return [dA, dB, dD, dL]
        
        res = solve_ivp(sweep_ode, t_eval_sweep, y0, method='Radau')
        D_final, L_final = res.y[2][-1], res.y[3][-1]
        tot = D_final + L_final
        ee_grid[i, j] = (abs(D_final - L_final) / tot * 100.0) if tot > 1e-6 else 0.0

# ==============================================================================
# PLOT FIGURES
# ==============================================================================
fig = plt.figure(figsize=(16, 9))

# 1. 24-hour %ee evolution plot
ax1 = plt.subplot(2, 2, 1)
ax1.plot(sol_fixed.t / 3600, ee_fixed, 'r--', linewidth=2, label='Fixed Feed ($ee$ Collapse)')
ax1.plot(sol_adapt.t / 3600, ee_adapt, 'b-', linewidth=2, label='Adaptive Dosing + Desorption Boost')
ax1.axhline(95.0, color='gray', linestyle=':', label='95% $ee$ Boundary Threshold')
ax1.set_title('%ee Evolution in Closed Loop over 24 Hours', fontsize=11)
ax1.set_xlabel('Time (hours)')
ax1.set_ylabel('Enantiomeric Excess (%)')
ax1.set_ylim([40, 102])
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='lower left')

# 2. Dynamics of [A] and Product [D] Concentration (Bleed Stream Saturation)
ax2 = plt.subplot(2, 2, 2)
ax2.plot(sol_adapt.t / 3600, sol_adapt.y[2], 'm-', linewidth=2, label='[D] Saturated via Bleed')
ax2.set_xlabel('Time (hours)')
ax2.set_ylabel('Product Concentration [D] (M)', color='m')
ax2.tick_params(axis='y', labelcolor='m')
ax2.grid(True, linestyle='--', alpha=0.6)

ax2_twin = ax2.twinx()
ax2_twin.plot(sol_fixed.t / 3600, sol_fixed.y[0], 'r--', label='[A] Fixed (Accumulation)')
ax2_twin.plot(sol_adapt.t / 3600, sol_adapt.y[0], 'g-', linewidth=2, label='[A] Adaptive (Protects Ultra-dilution)')
ax2_twin.axhline(5e-5, color='orange', linestyle=':', label='Ceiling Threshold 5e-5 M')
ax2_twin.set_ylabel('Precursor Concentration [A] (M)', color='g')
ax2_twin.set_yscale('log')
ax2_twin.tick_params(axis='y', labelcolor='g')
ax2.set_title('Product [D] Saturation and Precursor [A] Control', fontsize=11)

# Combine legends of both axes
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='center right')

# 3. Parameter Space Heatmap and Safe Boundary
ax3 = plt.subplot(2, 1, 2)
c = ax3.contourf(K_inh_range, k0_range, ee_grid, levels=np.linspace(50, 100, 26), cmap='viridis')
cbar = fig.colorbar(c, ax=ax3)
cbar.set_label('%ee achieved after 12 hours', rotation=270, labelpad=15)

# 95% contour line (Safe Operating Boundary)
contour_safe = ax3.contour(K_inh_range, k0_range, ee_grid, levels=[95.0], colors='red', linewidths=2.5)
ax3.clabel(contour_safe, inline=True, fmt='Safe Boundary (ee = 95%%)', fontsize=10)

ax3.set_title('Heatmap: Safe Operating Window as a function of $K_{inh}$ and $k_0$', fontsize=11)
ax3.set_xlabel('Product Inhibition Constant $K_{inh}$ (L/mol)')
ax3.set_ylabel('Background Racemic Rate Constant $k_0$ (L/(mol*s))')

plt.tight_layout()
plt.show()
