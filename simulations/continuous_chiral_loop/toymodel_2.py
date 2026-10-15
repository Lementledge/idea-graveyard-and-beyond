import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# ==============================================================================
# PHẦN 1 & 3 & 4: MÔ PHỎNG 24 GIỜ VỚI ADAPTIVE DOSING & DESORPTION BOOST
# ==============================================================================

# Thông số động học cơ sở
k0_base = 10.0         # Phản ứng racemic nền (L/(mol*s))
k_cat = 15.0          # Tốc độ quay vòng cực đại trên chiral bed (1/s)
K_A = 1000.0          # Ái lực hấp phụ của A (L/mol)
K_B = 1000.0          # Ái lực hấp phụ của B (L/mol)
K_inh_base = 50.0     # Ái lực bám gốc của sản phẩm (L/mol)

P_D_bed = 0.5         # Mật độ template D (mol/L)
P_L_bed = 0.005       # Tạp chất L (ee bed = 98%)

V_reactor = 1.0       # Thể tích vòng phản ứng (L)
F_feed_max = 1e-4     # Lưu lượng nạp tối đa (0.1 mL/s)
A_feed = 0.5          # Nồng độ trong syringe (M)
B_feed = 0.5
R_prod = 0.98         # Hệ số màng giữ lại sản phẩm (OSN)
F_bleed = 1e-5        # Dòng rút sản phẩm cô đặc (L/s)

# Tham số Desorption Boost: Hiệu ứng dòng rửa/lực cắt (shear flow) & gradient nhiệt
# K_inh_eff = K_inh_base / (1 + gamma_shear * v_flow + beta_temp * delta_T)
boost_factor = 2.5    # Giảm ái lực bám ngược 2.5 lần nhờ lực cắt và xung nhiệt
K_inh_eff = K_inh_base / boost_factor

# Hàm động học với bộ điều khiển Adaptive Dosing
def osn_system_ode(t, y, adaptive=True):
    A, B, D, L = max(y[0], 0), max(y[1], 0), max(y[2], 0), max(y[3], 0)
    
    # 1. Bộ điều khiển Adaptive Dosing: Hạ F_feed khi [A] vượt ngưỡng 5e-5 M
    A_threshold = 5e-5
    if adaptive:
        # Hàm sigmoid điều tiết mượt lưu lượng nạp bảo vệ điều kiện siêu loãng
        F_in = F_feed_max / (1.0 + np.exp((A - A_threshold) / (0.15 * A_threshold)))
    else:
        F_in = F_feed_max
        
    F_perm = max(F_in - F_bleed, 0)
    
    # 2. Hấp phụ Langmuir cạnh tranh có Desorption Boost
    denom = 1.0 + K_A * A + K_B * B + K_inh_eff * (D + L)
    theta_A = (K_A * A) / denom
    theta_B = (K_B * B) / denom
    
    # 3. Tốc độ phản ứng
    r_rac = k0_base * A * B
    r_cat_D = k_cat * P_D_bed * theta_A * theta_B
    r_cat_L = k_cat * P_L_bed * theta_A * theta_B
    
    # 4. Cân bằng vật chất (OSN loop)
    loss_A = (F_perm * (1.0 - 0.05) * A + F_bleed * A) / V_reactor
    loss_B = (F_perm * (1.0 - 0.05) * B + F_bleed * B) / V_reactor
    loss_D = (F_perm * (1.0 - R_prod) * D + F_bleed * D) / V_reactor
    loss_L = (F_perm * (1.0 - R_prod) * L + F_bleed * L) / V_reactor
    
    dA = (F_in * A_feed) / V_reactor - loss_A - r_rac - r_cat_D - r_cat_L
    dB = (F_in * B_feed) / V_reactor - loss_B - r_rac - r_cat_D - r_cat_L
    dD = 0.5 * r_rac + r_cat_D - loss_D
    dL = 0.5 * r_rac + r_cat_L - loss_L
    
    return [dA, dB, dD, dL]

# Chạy mô phỏng 24 giờ
t_span_24h = (0, 86400) # 24 giờ
t_eval_24h = np.linspace(0, 86400, 3000)
y0 = [0.0, 0.0, 1e-6, 1e-6]

# Kịch bản 1: Không có kiểm soát thích ứng (Fixed Dosing)
sol_fixed = solve_ivp(lambda t, y: osn_system_ode(t, y, adaptive=False),
                      t_span_24h, y0, t_eval=t_eval_24h, method='Radau')

# Kịch bản 2: Có kiểm soát thích ứng (Adaptive Dosing + Desorption Boost)
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
# PHẦN 2: QUÉT HEATMAP TÌM "VÙNG BIÊN AN TOÀN" (SAFE OPERATING WINDOW)
# ==============================================================================
print("Đang quét không gian tham số (K_inh x k0)...")
grid_res = 25
k0_range = np.linspace(1.0, 100.0, grid_res)
K_inh_range = np.linspace(0.0, 200.0, grid_res)
ee_grid = np.zeros((grid_res, grid_res))

# Đánh giá %ee tại thời điểm dừng 12 giờ
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
# HIỂN THỊ ĐỒ THỊ
# ==============================================================================
fig = plt.figure(figsize=(16, 9))

# 1. Đồ thị tiến hóa %ee qua 24 giờ
ax1 = plt.subplot(2, 2, 1)
ax1.plot(sol_fixed.t / 3600, ee_fixed, 'r--', linewidth=2, label='Fixed Feed (Bị sụp đổ $ee$)')
ax1.plot(sol_adapt.t / 3600, ee_adapt, 'b-', linewidth=2, label='Adaptive Dosing + Desorption Boost')
ax1.axhline(95.0, color='gray', linestyle=':', label='Ngưỡng biên 95% $ee$')
ax1.set_title('Tiến hóa %ee trong vòng lặp kín suốt 24 giờ', fontsize=11)
ax1.set_xlabel('Thời gian (giờ)')
ax1.set_ylabel('Enantiomeric Excess (%)')
ax1.set_ylim([40, 102])
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc='lower left')

# 2. Động thái nồng độ [A] và Sản phẩm [D] (Bão hòa dòng Bleed)
ax2 = plt.subplot(2, 2, 2)
ax2.plot(sol_adapt.t / 3600, sol_adapt.y[2], 'm-', linewidth=2, label='[D] Bão hòa qua Bleed')
ax2.set_xlabel('Thời gian (giờ)')
ax2.set_ylabel('Nồng độ Sản phẩm [D] (M)', color='m')
ax2.tick_params(axis='y', labelcolor='m')
ax2.grid(True, linestyle='--', alpha=0.6)

ax2_twin = ax2.twinx()
ax2_twin.plot(sol_fixed.t / 3600, sol_fixed.y[0], 'r--', label='[A] Fixed (Ứ đọng)')
ax2_twin.plot(sol_adapt.t / 3600, sol_adapt.y[0], 'g-', linewidth=2, label='[A] Adaptive (Bảo vệ siêu loãng)')
ax2_twin.axhline(5e-5, color='orange', linestyle=':', label='Ngưỡng trần 5e-5 M')
ax2_twin.set_ylabel('Nồng độ Tiền chất [A] (M)', color='g')
ax2_twin.set_yscale('log')
ax2_twin.tick_params(axis='y', labelcolor='g')
ax2.set_title('Bão hòa Sản phẩm [D] và Khống chế Tiền chất [A]', fontsize=11)

# Gộp chú thích 2 trục
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='center right')

# 3. Heatmap không gian tham số và Vùng biên an toàn
ax3 = plt.subplot(2, 1, 2)
c = ax3.contourf(K_inh_range, k0_range, ee_grid, levels=np.linspace(50, 100, 26), cmap='viridis')
cbar = fig.colorbar(c, ax=ax3)
cbar.set_label('%ee đạt được sau 12 giờ', rotation=270, labelpad=15)

# Đường đẳng mức 95% (Safe Operating Boundary)
contour_safe = ax3.contour(K_inh_range, k0_range, ee_grid, levels=[95.0], colors='red', linewidths=2.5)
ax3.clabel(contour_safe, inline=True, fmt='Safe Boundary (ee = 95%%)', fontsize=10)

ax3.set_title('Heatmap: Vùng biên vận hành an toàn (Safe Operating Window) theo $K_{inh}$ và $k_0$', fontsize=11)
ax3.set_xlabel('Hằng số ức chế sản phẩm $K_{inh}$ (L/mol)')
ax3.set_ylabel('Hằng số racemic nền $k_0$ (L/(mol*s))')

plt.tight_layout()
plt.show()