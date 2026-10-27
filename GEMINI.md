# OpenCourant Simulation & Modeling Invariants

## 1. Solver Execution & Threading
- **Hardware Profile:** AMD Ryzen 9 7900X (24 logical cores).
- **Execution Flags:** Always run OpenCourant with `-nt 24`.
- **Environment Variables:** Set `OMP_NUM_THREADS=24` and `KMP_STACKSIZE=400m`.
- **Python Execution:** Always invoke Python scripts via conda environment:
  `C:\Users\rossi\miniconda3\condabin\conda.bat run -n puncturing python <script.py>`.

## 2. Contact Interface Standards
- **Honeycomb Foil-to-Laminate Contact:** NEVER use `/INTER/TYPE7` node-to-surface between vertical foil shells and horizontal composite laminate faces. Use `/INTER/TYPE19` (Edge-to-Surface) with:
  - Master Surface: Composite skin inner face (`/SURF/PART/EXT`).
  - Secondary Set: Foil shell part (`/SURF/PART`).
  - Parameters: `Iedge = 1`, `z_offset = 0.050 mm` physical clearance, `Gapmin = 0.010 mm`, `INACTIV = 0` (never `1`, which deactivates contact stiffness on initial penetrations), friction $\mu \approx 0.15 - 0.20$.
  - Indenter Contact (`/INTER/TYPE7/1`): Secondary set must include all laminate and foil nodes in the puncture zone ($r \le 28.0\text{ mm}$) to prevent indenter mesh penetration through eroded plies.
- **Foil Self-Contact:** Always pair with `/INTER/TYPE7/4` self-contact (`INACTIV = 1`) among foil shells to capture progressive accordion folding.

## 3. Symmetry & Multi-Scale Conventions
- **Quarter Models ($x \ge 0, y \ge 0$):**
  - Boundary constraint on $x = 0$: `100 011` ($U_x = 0, \theta_y = \theta_z = 0$).
  - Boundary constraint on $y = 0$: `010 101` ($U_y = 0, \theta_x = \theta_z = 0$).
  - Die aperture fixture ($z = 0, r \ge 15.0\text{ mm}$): `111 111`.
  - Indenter master node: `110 111` ($U_z$ displacement only).
  - Reaction Force & Energy Post-Processing: Automatically multiply by $4.0\times$.

## 4. Radioss Card Formatting & Starter Verification
- **Card Alignment in `/PROP/TYPE6`:** Ensure exactly 4 cards for standard orthotropic solids:
  - Card 1: `Isolid, Ismstr, Icpre, Itetra`
  - Card 2: `qa, qb, h, omega`
  - Card 3: `dir, skew_id, frame_id`
  - Card 4: `theta, phi` (Card 5 `deltaT_min` must remain default 0.0 unless explicit erosion is intended).
- **Verification Rule:** Always inspect starter `.out` file to verify zero errors and confirm that `BRICK MINIMUM TIME STEP = 0.000000000000` across all plies prior to engine launch.

## 5. Time Integration & Mass Scaling
- Target time step: $\Delta t \approx 1.0 \times 10^{-7}\text{ s}$ via `/DT/NODA/CST`.
- Maximum allowable mass addition: $\Delta M / M \le 1.0\%$.
- Erosion time step threshold: `/DT/BRICK/DEL` and `/DT/SHELL/DEL` must be set below physical acoustic step ($\le 1.0 \times 10^{-9}\text{ s}$) to prevent cycle 0 element deletion.
