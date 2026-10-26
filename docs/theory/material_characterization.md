# Material Characterization & Parameter Derivation

This document details the derivation of material parameters for the finite element simulation of the sandwich panel puncture test using OpenCourant (explicit solver).

---

## 1. CFRP Face Sheets: CIT CF306 12K T700 T2/2 ET445 40%

### 1.1 Datasheet Properties Summary
* **Fiber:** Torayca T700S 12K
* **Weave style:** Twill 2×2 (balanced fabric)
* **Resin system:** ET445 epoxy (40% weight content)
* **Dry fabric areal weight:** $300\text{ g/m}^2 \ (\pm 4\%)$
* **Prepreg nominal areal weight:** $500\text{ g/m}^2$
* **Cured Ply Thickness (CPT):** $t_{\text{ply}} = 0.333\text{ mm}$
* **Layup:** $[0^\circ/45^\circ/0^\circ/45^\circ/0^\circ/45^\circ/0^\circ]$ (7 plies)
* **Total skin thickness:** $h_{\text{skin}} = 7 \times 0.333\text{ mm} = 2.331\text{ mm}$

### 1.2 Mechanical Properties (Twill 2×2 Fabric)
From mechanical characterization tests cured at standard autoclave conditions ($125^\circ\text{C}$, 6 bar):

| Property | Symbol | Value | Unit |
|---|---|---|---|
| Tensile Modulus (0°) | $E_{11}^t$ | 56.0 | GPa |
| Tensile Strength (0°) | $X_t$ | 925 | MPa |
| Elongation at Break (0°) | $\epsilon_{11}^{u,t}$ | 1.46 | % |
| Poisson's Ratio (0°-90°) | $\nu_{12}$ | 0.05 | - |
| Tensile Modulus (90°) | $E_{22}^t$ | 56.5 | GPa |
| Tensile Strength (90°) | $X_{t,90}$ | 1026 | MPa |
| Elongation at Break (90°) | $\epsilon_{22}^{u,t}$ | 1.58 | % |
| Compressive Modulus (0°) | $E_{11}^c$ | 49.7 | GPa |
| Compressive Strength (0°) | $X_c$ | 559 | MPa |
| Compressive Modulus (90°) | $E_{22}^c$ | 50.1 | GPa |
| Compressive Strength (90°) | $Y_c$ | 599 | MPa |
| Flexural Modulus (0°) | $E_{\text{flex},0}$ | 50.9 | GPa |
| Flexural Strength (0°) | $\sigma_{\text{flex},0}$ | 976 | MPa |
| In-plane Shear Modulus | $G_{12}$ | 2.99 | GPa |
| In-plane Shear Strength (peak) | $S_{12}$ | 104 | MPa |
| In-plane Shear Strength (@5%) | $S_{12,5\%}$ | 58.6 | MPa |
| Density | $\rho$ | $1500$ | $\text{kg/m}^3$ |

### 1.3 Out-of-Plane Engineering Constants (Transverse Isotropy / Orthotropy)
For 3D solid elements, transverse properties are derived using standard composite micromechanics and typical resin-dominated transverse response:
* $E_{33} \approx E_{\text{resin}} / (1 - V_f) \approx 7.5\text{ GPa}$
* $G_{13} \approx G_{23} \approx 2.8\text{ GPa}$
* $\nu_{13} \approx \nu_{23} \approx 0.30$
* Transverse shear strengths: $S_{13} \approx S_{23} \approx 65\text{ MPa}$
* Out-of-plane tensile strength: $Z_t \approx 50\text{ MPa}$
* Out-of-plane compressive strength: $Z_c \approx 450\text{ MPa}$

---

## 2. Aluminium Honeycomb Core: Alloy 5052 - 1/8" - 6.1 pcf

### 2.1 Specification
* **Alloy:** Aluminium 5052
* **Cell size:** $d_{\text{cell}} = 1/8\text{ inch} = 3.175\text{ mm}$
* **Foil thickness:** $t_{\text{foil}} = 0.0015\text{ inch} = 0.0381\text{ mm}$
* **Nominal density:** $\rho = 6.1\text{ pcf} = 97.6\text{ kg/m}^3 \approx 9.76 \times 10^{-11}\text{ tonne/mm}^3$
* **Core height:** $H_{\text{core}} = 15.0\text{ mm}$

### 2.2 Homogenized Equivalent Orthotropic Properties
From IMATEC datasheet:

| Property | Symbol | Value | Unit (SI) | Value (mm, N, s, tonne) |
|---|---|---|---|---|
| Density | $\rho$ | 97.6 | $\text{kg/m}^3$ | $9.76 \times 10^{-11}\text{ tonne/mm}^3$ |
| Out-of-plane Modulus ($T$, axis 3) | $E_{33}$ | 1654.7 | MPa | $1654.7\text{ MPa}$ |
| Out-of-plane Bare Compressive Strength | $\sigma_{33}^{\text{bare}}$ | 6.00 | MPa | $6.00\text{ MPa}$ |
| Out-of-plane Crush Strength | $\sigma_{\text{crush}}$ | 3.10 | MPa | $3.10\text{ MPa}$ |
| In-plane Shear Modulus ($L$, axis 1-3) | $G_{13} = G_{TL}$ | 675.7 | MPa | $675.7\text{ MPa}$ |
| In-plane Shear Modulus ($W$, axis 2-3) | $G_{23} = G_{TW}$ | 282.7 | MPa | $282.7\text{ MPa}$ |
| Shear Strength ($L$ direction) | $\tau_{13}^{\text{ult}}$ | 3.48 | MPa | $3.48\text{ MPa}$ |
| Shear Strength ($W$ direction) | $\tau_{23}^{\text{ult}}$ | 2.21 | MPa | $2.21\text{ MPa}$ |
| In-plane Young's Moduli ($L$, $W$) | $E_{11}, E_{22}$ | $\approx 5.0$ | MPa | $5.0\text{ MPa}$ (very compliant in-plane) |
| In-plane Shear Modulus ($L-W$) | $G_{12}$ | $\approx 2.0$ | MPa | $2.0\text{ MPa}$ |

### 2.3 Meso-scale Aluminium 5052-H39 Base Alloy Properties
For the Phase 2 cell-wall shell elements:
* Density: $\rho_{\text{Al}} = 2680\text{ kg/m}^3$
* Young's Modulus: $E = 70\text{ GPa}$
* Poisson's ratio: $\nu = 0.33$
* Yield stress: $\sigma_y = 255\text{ MPa}$
* Ultimate tensile strength: $\sigma_u = 300\text{ MPa}$
* Elongation at break: $\epsilon_f = 0.08$

---

## 3. Cohesive Interfaces (Delamination and Debonding)

Bilinear traction-separation law with mixed-mode Benzeggagh-Kenane (B-K) failure criterion:
* **Skin-to-Core interface (Adhesive fillet):**
  * Penalty stiffness: $K_n = K_s = K_t = 1.0 \times 10^5\text{ N/mm}^3$
  * Interfacial normal strength: $t_n^0 = 15.0\text{ MPa}$
  * Interfacial shear strength: $t_s^0 = 20.0\text{ MPa}$
  * Mode I fracture energy: $G_{Ic} = 0.80\text{ kJ/m}^2 = 0.80\text{ N/mm}$
  * Mode II fracture energy: $G_{IIc} = 1.50\text{ kJ/m}^2 = 1.50\text{ N/mm}$
  * B-K parameter: $\eta = 1.75$

* **Inter-ply interface (within 7-ply CFRP skin):**
  * Penalty stiffness: $K_n = K_s = 1.0 \times 10^6\text{ N/mm}^3$
  * Normal interlaminar tensile strength: $t_n^0 = 50.0\text{ MPa}$
  * Interlaminar shear strength: $t_s^0 = 65.0\text{ MPa}$
  * Mode I fracture energy: $G_{Ic} = 0.35\text{ kJ/m}^2 = 0.35\text{ N/mm}$
  * Mode II fracture energy: $G_{IIc} = 1.00\text{ kJ/m}^2 = 1.00\text{ N/mm}$
  * B-K parameter: $\eta = 1.75$

---

## 4. Consistent System of Units

All explicit FE input decks and scripts adhere strictly to the standard dynamic structural unit system:

$$\text{Length: mm} \quad|\quad \text{Time: s} \quad|\quad \text{Mass: tonne} \ (10^3\text{ kg}) \quad|\quad \text{Force: N} \quad|\quad \text{Stress/Modulus: MPa} \quad|\quad \text{Energy: mJ}$$

| Quantity | SI Unit | Simulation Unit | Conversion Factor |
|---|---|---|---|
| Length | $\text{m}$ | $\text{mm}$ | $10^3$ |
| Mass | $\text{kg}$ | $\text{tonne}$ | $10^{-3}$ |
| Time | $\text{s}$ | $\text{s}$ | $1$ |
| Force | $\text{N}$ | $\text{N}$ | $1$ |
| Stress / Pressure | $\text{Pa}$ | $\text{MPa}$ ($\text{N/mm}^2$) | $10^{-6}$ |
| Energy | $\text{J}$ | $\text{mJ}$ ($\text{N}\cdot\text{mm}$) | $10^3$ |
| Density | $\text{kg/m}^3$ | $\text{tonne/mm}^3$ | $10^{-12}$ |
