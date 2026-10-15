# Continuous Super-Dilution Micro-Infusion for Stereoselective Autocatalysis

> **One-sentence Abstract:** A continuous-flow reaction architecture that suppresses uncatalyzed racemic background pathways via dynamic super-dilution, mitigates product inhibition via shear-induced desorption, and resolves osmotic membrane pressure limits through a decoupled micro-concentrator and MSMPR crystallizer[cite: 5].

- **Status:** Toy Model Available
- **Domain:** Nature / Prebiotic Chemistry / Chemical Reaction Engineering
- **Primary Bottleneck:** Wet-Lab Validation of Shear-Induced Desorption Kinetics & PEEK Micro-Channel Fabrication
- **Created Date:** 2026-10-12

---

## 1. Context & Motivation
- **The Problem:** In asymmetric autocatalysis, the stereoselective pathway continuously competes against the uncatalyzed racemic background reaction[cite: 5]. In traditional batch reactors, high initial concentrations of precursors ($0.1 - 1.0\text{ M}$) quadratically accelerate the background reaction ($r_{rac} = k_0 [A][B]$), destroying the enantiomeric excess ($ee$)[cite: 5].
- **Failure of Mainstream Approaches:** The classical workaround is cryogenic cooling (e.g., $-78^\circ\text{C}$) to suppress the racemic pathway, which severely diminishes the catalytic turnover rate and is energy-intensive[cite: 5]. 

---

## 2. Core Hypothesis & Mechanics

### 1. Dynamic Super-Dilution & Dual-Site Langmuir Kinetics
By injecting precursors via an Adaptive Dosing Controller (using a smooth Sigmoid function), free precursor concentrations are artificially choked below $5 \times 10^{-5}\text{ M}$[cite: 5]. At this scale, bulk bimolecular collisions are kinetically suffocated, while the template-directed reaction proceeds at pseudo-first-order kinetics over a high-density chiral bed[cite: 5, 7].

### 2. Shear-Induced Desorption Boost
A primary barrier in autocatalysis is Product Inhibition, where the generated chiral product strongly adsorbs to the template, poisoning the active sites[cite: 5]. By maintaining a high-velocity recirculating flow ($v_{loop} \approx 3.0\text{ m/s}$), the hydrodynamic wall shear stress physically strips the product from the template, effectively reducing the effective inhibition constant ($K_{inh,eff}$) by over $90\%$[cite: 5, 7].

### 3. Decoupled Flowsheet Architecture (Solving the Osmotic Paradox)
A single-loop system faces a fatal "Osmotic Paradox": as product accumulates ($[D] \approx 1.5\text{ M}$), the osmotic pressure ($\Delta \pi$) spikes to $\sim 36.4\text{ bar}$, exceeding the mechanical rupture limit ($30\text{ bar}$) of Organic Solvent Nanofiltration (OSN) membranes[cite: 5, 8]. The validated toy model solves this via a 3-stage decoupled architecture[cite: 5, 10]:
- **Stage 1 (Main Reaction Loop):** Operates at high velocity and low steady-state concentration ($[D]_1 \approx 0.35 - 0.55\text{ M}$) to keep total membrane pressure safe ($13 - 15\text{ bar}$)[cite: 5].
- **Stage 2 (Micro-Falling Film Concentrator):** A $15\text{ mL}$ micro-chamber that receives the bleed stream ($F_{bleed}$) and evaporates the solvent, driving the concentration up to $2.62\text{ M}$ without inducing racemic background reactions (since free $[A]$ and $[B]$ are nearly zero)[cite: 5, 11].
- **Stage 3 (MSMPR Crystallizer):** The concentrated stream is continuously cooled to $5^\circ\text{C}$, yielding solid enantiopure crystals ($> 99.9\% ee$) through conglomerate crystallization at a steady rate of $\approx 7.5\text{ g/h}$[cite: 5, 12].

---

## 3. Potential Impact & Value
- **Scalable Room-Temperature Synthesis:** Eliminates the need for cryogenic energy expenditures by substituting thermodynamic temperature control with kinetic dilution control[cite: 5].
- **Validated Pre-charging:** By pre-charging the reactor with a $0.35\text{ M}$ chiral seed, the startup lag to achieve crystallization is computationally proven to drop from 15 hours to just 1.5 hours[cite: 5, 12].

---

## 4. The Bottlenecks & Open Questions

- **Wet-Lab Emulation of Shear Stress:** The parameter $\alpha_{shear}$ dictates the desorption boost[cite: 5]. Validating this exact coefficient requires precise LC-MS measurements of the dissociation constant ($k_{off}$) under varying microfluidic flow rates ($0.5$ to $5.0\text{ mL/min}$)[cite: 5].
- **Crystallization Metastable Zone Width (MSZW):** Preventing premature crystallization and channel clogging inside the transfer lines before the fluid reaches the MSMPR centrifuge[cite: 5].

---

## 5. Potential Attack Vectors & Next Steps

- **Model Reaction System:** Benchmark the continuous loop using the Soai reaction (diisopropylzinc and pyrimidine-5-carbaldehyde) or a direct asymmetric aldol addition using immobilized proline derivatives on a porous polymer packed bed[cite: 5].
- **Hardware Fabrication:** Construct the fluidic channels using high-pressure inert materials like PEEK or borosilicate glass[cite: 5].
- **In-Line Process Analytical Technology (PAT):** Integrate an in-line micro-polarimeter or Circular Dichroism (CD) flow cell at the harvest stream to monitor $\%ee$ in real-time without disrupting the closed loop[cite: 5].

---

## 6. References & Prior Art
- **Frank, F. C. (1953):** On spontaneous asymmetric synthesis. Biochimica et Biophysica Acta, 11, 459-463.
- **Soai, K., Shibata, T., Morioka, H., & Choji, K. (1995):** Asymmetric autocatalysis and amplification of enantiomeric excess of a chiral molecule. Nature, 378(6559), 767-768.
- **Marchetti, P., Jimenez Solomon, M. F., Szekely, G., & Livingston, A. G. (2014):** Molecular separation with organic solvent nanofiltration: A critical review. Chemical Reviews, 114(21), 10735-10806.
