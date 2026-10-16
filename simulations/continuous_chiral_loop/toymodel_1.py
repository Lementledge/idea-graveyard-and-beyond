import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- 1. KINETIC & ADSORPTION PARAMETERS ---
k0 = 10.0         # Strong second-order background racemic reaction (L/(mol*s))
k_cat = 15.0      # Maximum turnover frequency on chiral bed (1/s)
K_A = 1000.0      # Adsorption affinity constant of A (L/mol)
K_B = 1000.0      # Adsorption affinity constant of B (L/mol)

# Re-binding affinity of product to template bed (Product Inhibition)
K_inh = 20.0      # L/mol (K_D = K_L = K_inh)

P_D_bed = 0.5     # Template D density
P_L_bed = 0.005   # Impurity L (bed ee = 98%)

# --- 2. OPERATING PARAMETERS & OSN MEMBRANE ---
V_reactor = 1.0   # L
F_feed = 1e-4     # 0.1 mL/s = 1e-4 L/s
A_feed = 0.5      # M
B_feed = 0.5      # M

R_A = 0.05
R_B = 0.05
R_prod = 0.98

F_bleed = 1e-5    # Concentrated product bleed flow rate
F_permeate = F_feed - F_bleed

# --- 3. GENERAL DIFFERENTIAL EQUATIONS FOR BOTH CASES ---
def closed_loop_ode(t, y, use_inhibition=True):
    A, B, D, L = max(y[0], 0), max(y[1], 0), max(y[2], 0), max(y[3], 0)
    
    # Calculate competitive Langmuir denominator
    if use_inhibition:
        denom = 1.0 + K_A * A + K_B * B + K_inh * D + K_inh * L
    else:
        denom = 1.0 + K_A * A + K_B * B
        
    theta_A = (K_A * A) / denom
    theta_B = (K_B * B) / denom
    
    r_rac = k0 * A * B
    r_cat_D = k_cat * P_D_bed * theta_A * theta_B
    r_cat_L = k_cat * P_L_bed * theta_A * theta_B
    
    loss_A = (F_permeate * (1.0 - R_A) * A + F_bleed * A) / V_reactor
    loss_B = (F_permeate * (1.0 - R_B) * B + F_bleed * B) / V_reactor
    loss_D = (F_permeate * (1.0 - R_prod) * D + F_bleed * D) / V_reactor
    loss_L = (F_permeate * (1.0 - R_prod) * L + F_bleed * L) / V_reactor
    
    dA = (F_feed * A_feed) / V_reactor - loss_A - r_rac - r_cat_D - r_cat_L
    dB = (F_feed * B_feed) / V_reactor - loss_B - r_rac - r_cat_D - r_cat_L
    dD = 0.5 * r_rac + r_cat_D - loss_D
    dL = 0.5 * r_rac + r_cat_L - loss_L
    
    return [dA, dB, dD, dL]

t_span = (0, 14400) # 4 hours
t_eval = np.linspace(t_span[0], t_span[1], 2000)
y0 = [0.0, 0.0, 1e-6, 1e-6]

# Run simulation for 2 scenarios: With and Without Product Inhibition
sol_ideal = solve_ivp(lambda t, y: closed_loop_ode(t, y, use_inhibition=False), 
                      t_span, y0, t_eval=t_eval, method='Radau')

sol_inh = solve_ivp(lambda t, y: closed_loop_ode(t, y, use_inhibition=True), 
                    t_span, y0, t_eval=t_eval, method='Radau')

# --- 4. CALCULATE %ee AND STATISTICS ---
def get_ee(sol):
    D, L = sol.y[2], sol.y[3]
    total = D + L
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(total > 1e-7, (np.abs(D - L) / total) * 100.0, 0.0)

ee_ideal = get_ee(sol_ideal)
ee_inh = get_ee(sol_inh)

# --- 5. PLOT COMPARISON GRAPHS ---
fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

# Plot 1: Compare %ee
axes[0].plot(sol_ideal.t / 3600, ee_ideal, 'b--', label='Ideal ($K_{inh}=0$)')
axes[0].plot(sol_inh.t / 3600, ee_inh, 'r-', linewidth=2, label='With Inhibition ($K_{inh}=20$)')
axes[0].set_title('Impact of Product Inhibition on %ee', fontsize=11)
axes[0].set_xlabel('Operating Time (hours)')
axes[0].set_ylabel('Enantiomeric Excess (%)')
axes[0].set_ylim([70, 100])
axes[0].grid(True, linestyle='--', alpha=0.6)
axes[0].legend()

# Plot 2: Dynamics of precursor concentration [A]
axes[1].plot(sol_ideal.t / 3600, sol_ideal.y[0], 'b--', label='[A] Ideal')
axes[1].plot(sol_inh.t / 3600, sol_inh.y[0], 'r-', linewidth=2, label='[A] Accumulated due to inhibition')
axes[1].set_title('Free Precursor Concentration [A] in Loop', fontsize=11)
axes[1].set_xlabel('Operating Time (hours)')
axes[1].set_ylabel('Concentration (M)')
axes[1].set_yscale('log')
axes[1].grid(True, linestyle='--', alpha=0.6)
axes[1].legend()

# Plot 3: Accumulated product [D] yield
axes[2].plot(sol_ideal.t / 3600, sol_ideal.y[2], 'b--', label='[D] Ideal')
axes[2].plot(sol_inh.t / 3600, sol_inh.y[2], 'r-', linewidth=2, label='[D] With inhibition')
axes[2].set_title('Accumulated Product [D] Concentration in Tank', fontsize=11)
axes[2].set_xlabel('Operating Time (hours)')
axes[2].set_ylabel('Concentration (M)')
axes[2].grid(True, linestyle='--', alpha=0.6)
axes[2].legend()

plt.tight_layout()
plt.show()
