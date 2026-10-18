# Aerodynamic Kinetic Transport Index: 100-Vehicle Empirical Verification and Asymptotic Aerodynamic Saturation

> **One-sentence Abstract:** An invariant transport metric defined by the dimension [M]^-1 [L] (m/kg in SI) that penalizes brute-force powertrain scaling and isolates aerodynamic streamline purity by demonstrating that aerodynamic drag losses (v^2) cancel out raw velocity gains (v^2) into an asymptotic limit (21.159 / (Cd·A)) with Pearson r = 0.9778 across 100 empirical vehicles.

- **Status:** Toy Model Available
- **Domain:** Nature / Applied Physics / Vehicle Dynamics & Fluid Mechanics
- **Primary Bottleneck:** Empirical High-Speed Yaw-Angle Validation & Active Aerodynamic Hysteresis
- **Created Date:** 2026-10-17

---

## 1. Context & Motivation

- **The Brute-Force Powertrain Trap:** Modern automotive engineering evaluates vehicle efficiency via disjointed metrics:
  1. *Acceleration & Peak Velocity:* 0-100 km/h acceleration or top speed, completely disregarding thermodynamic dissipation.
  2. *Standard Driving Cycles (WLTP / EPA):* Skewed heavily toward low-speed urban regimes where inertia and rolling friction dominate, masking the exponential drag penalties of large frontal areas (e.g., heavy electric SUVs).
- **The Physical Objective:** Establish a unified, closed-form mechanical figure of merit that rewards aerodynamic streamline quality and kinetic conservation rather than raw engine torque or oversized battery packs.

---

## 2. Core Hypothesis & Mathematical Formulation

### 1. The Metric Definition
$$\text{Index} = v^2 \times \frac{d}{E} = \frac{v^2}{E/d} \quad \left[\frac{\text{km}^3}{\text{h}^2 \cdot \text{kJ}}\right] \implies \frac{\text{m}}{\text{kg}} \text{ (SI units)}$$

- $v^2$: Velocity squared, serving as the kinetic velocity reward.
- $d/E$: Specific distance per unit energy consumed (inverse of tractive energy expenditure).
- Dimensional reduction:
  $$[\text{Dim}] = \frac{[\text{L}]^3}{[\text{T}]^2 \cdot ([\text{M}][\text{L}]^2[\text{T}]^{-2})} = \frac{[\text{L}]}{[\text{M}]} \implies \frac{\text{m}}{\text{kg}}$$
  Physical meaning: The effective distance displacement achieved per unit of aerodynamic and inertial resisting mass. $1\text{ m/kg} \approx 12.96\text{ km}^3/(\text{h}^2 \cdot \text{kJ})$.

### 2. Quadratic Cancellation and the Asymptotic Limit
Tractive road force under constant cruise:
$$F_{\text{total}} = F_{\text{rr}} + F_{\text{aero}} = C_{\text{rr}} m g + \frac{1}{2} \rho (C_d A) v^2 \quad [\text{N} \equiv \text{kJ/km}]$$

At high highway speeds ($v \ge 100\text{--}120\text{ km/h}$), aerodynamic drag accounts for $>70\%$ of total tractive demand. Thus:
$$\lim_{v \to \infty} \text{Index} = \frac{v^2}{\frac{1}{2} \rho C_d A v^2} = \frac{2}{\rho C_d A} \quad [\text{m/kg}]$$

Taking air density at standard sea level ($\rho = 1.225\text{ kg/m}^3$ at $15^\circ\text{C}$):
$$\text{Index}_{\infty} = \frac{25.92}{1.225 \cdot C_d A} \approx \frac{21.159}{C_d A} \quad \left[\frac{\text{km}^3}{\text{h}^2 \cdot \text{kJ}}\right]$$

**The Saturation Invariant:** In the aerodynamic regime, raw motor power cannot inflate the score. Numerator ($v^2$) and aerodynamic energy losses ($E/d \propto v^2$) rise in lockstep and cancel each other out, locking the vehicle score into a geometric ceiling inversely proportional to aerodynamic drag area ($C_d A$).

---

## 3. Empirical Verification: 100-Vehicle Multi-Segment Benchmark

The model was tested across an empirical dataset of 100 production and concept vehicles spanning 10 archetypes from $20\text{ km/h}$ to $200\text{ km/h}$:

### 1. Statistical Correlation Convergence
The Pearson correlation coefficient ($r$) between the measured $\text{Index}(v)$ and the theoretical geometric limit $1/(C_d A)$ demonstrates progressive convergence:
- **At 20 km/h:** $r = 0.7486$ (Rolling resistance $F_{\text{rr}}$ dominates $>90\%$; Index acts as a parabola: $Index \approx v^2 / C_{\text{rr}} m g$).
- **At 60 km/h:** $r = 0.8917$ (Dynamic transition zone; $v_{50\%}$ crossover where $F_{\text{aero}} = F_{\text{rr}}$ occurs between $50$ and $72\text{ km/h}$).
- **At 120 km/h:** $r = 0.9778$ (Spearman rank $r = 0.9480$; saturation level reaches $73.8\%$).
- **At 200 km/h:** $r = 0.9959$ (Near-perfect convergence; saturation reaches $88.6\%$).

### 2. Segment Archetype Performance Hierarchy
- **Teardrop Hypermilers:** Aptera Launch Edition ($C_d = 0.130, C_d A = 0.240\text{ m}^2$) achieved an asymptotic Index of $87.98$ ($6.79\text{ m/kg}$), followed by the Volkswagen XL1 ($79.97$).
- **Aero Sedans vs. Electric SUVs:** Despite identical battery/motor efficiency, aerodynamic sedans (Lucid Air: $45.51$, Tesla Model 3 Highland: $43.52$) doubled the scores of electric SUVs (Tesla Model X: $32.65$, Audi Q8 e-tron: $29.56$) due to frontal area penalties ($A > 2.6\text{ m}^2$).
- **The Downforce Penalty Paradox:** The track-focused Porsche 911 GT3 RS (992), despite possessing 525 hp, incurs severe induced drag from its rear wing ($C_d = 0.390, C_d A = 0.84\text{ m}^2$), capping its asymptotic Index at $25.23$—lower than a standard Toyota Corolla ($34.82$) or BMW 320i ($41.44$).

---

## 4. Theoretical Extension: Universal Regularized Index

To resolve the low-speed rolling friction singularity ($v < 50\text{ km/h}$) where vehicle mass $m$ distorts aerodynamic invariance, the **Universal Regularized Index** is formulated by subtracting mechanical rolling resistance work:

$$\text{Index}_{\text{reg}} = \frac{v^2}{(E/d) - C_{\text{rr}} \cdot m \cdot g} \equiv \frac{2}{\rho \cdot C_d A} \quad [\text{m/kg}]$$

- **Speed-Invariance:** $\text{Index}_{\text{reg}}$ forms a perfectly flat horizontal line across all velocities ($0\text{ to }250\text{ km/h}$).
- **Decoupled Physics:** Separates tire/road contact mechanics from aerodynamic shape optimization, allowing direct benchmarking between vehicles of vastly different curb weights.

---

## 5. Artifacts & Reproducible Code

The empirical dataset and numerical analysis are fully reproducible:
- **Jupyter Notebook:** `simulations/aerodynamic-transport-index/reproducible_aerodynamic_transport_index.ipynb`
- **Technical Report:** `simulations/aerodynamic-transport-index/Aerodynamic_Kinetic_Transport_Index_Report.pdf`
- **Dependencies:** `numpy`, `pandas`, `matplotlib`

---

## 6. References & Prior Art

- **Gabrielli, G., & von Kármán, T. (1950):** What price speed? Specific power required for propulsion of vehicles. Mechanical Engineering, 72(10), 775-781.
- **Hucho, W. H. (1998):** Aerodynamics of Road Vehicles: From Fluid Mechanics to Vehicle Engineering (4th ed.). SAE International.
- **MacCready, P. B. (1981):** Vehicle efficiency and design optimization for ultra-low drag transport systems. SAE Technical Paper 810187.
- **Sovran, G., & Bohn, M. S. (1981):** Formulae for the Traction and Energy Requirements of Vehicles in General Urban Driving. SAE Transactions, 90, 876-896.
