"""
Phase 1: Homogenized Core Model Generator
Generates full 3D OpenCourant input decks (Starter _0000.rad and Engine _0001.rad)
for the CFRP / Aluminium Honeycomb Sandwich Puncture Simulation.
"""

from pathlib import Path
import numpy as np
import sys

# Ensure local imports work
sys.path.append(str(Path(__file__).resolve().parent))
from radioss_writer import RadiossDeck

def build_phase1_deck(
    panel_l: float = 100.0,
    panel_w: float = 100.0,
    n_inplane_fine: int = 40,
    n_inplane_coarse: int = 15,
    r_fine: float = 22.0,
    punch_dia: float = 25.0,
    aperture_dia: float = 30.0,
    v_punch: float = 1000.0, # mm/s = 1.0 m/s for explicit quasi-static
    t_end: float = 0.016,    # 16 ms -> 16 mm displacement
) -> tuple[RadiossDeck, dict]:
    """
    Constructs the FE model for Phase 1.
    All units in: mm, s, Mg (tonne), N, MPa, mJ
    """
    deck = RadiossDeck(title="CFRP_HONEYCOMB_PUNCTURE_PHASE1")

    # Geometry parameters
    t_ply = 0.333 # mm
    n_plies = 7
    t_skin = n_plies * t_ply # 2.331 mm
    h_core = 15.0 # mm
    r_punch = punch_dia / 2.0 # 12.5 mm
    r_aper = aperture_dia / 2.0 # 15.0 mm

    z_bot_skin_min = 0.0
    z_bot_skin_max = t_skin
    z_core_min = z_bot_skin_max
    z_core_max = z_core_min + h_core
    z_top_skin_min = z_core_max
    z_top_skin_max = z_top_skin_min + t_skin

    # Discretization
    # In-plane mesh: Cartesian grid centered at (0,0)
    # Fine grid from -r_fine to +r_fine with dx_fine
    # Transition to -50..+50 with graded dx
    fine_coords = np.linspace(-r_fine, r_fine, n_inplane_fine + 1)
    dx_fine = fine_coords[1] - fine_coords[0]

    # Coarse border coords
    left_coords = np.geomspace(50.0 - r_fine, dx_fine, n_inplane_coarse + 1)[::-1]
    left_coords = -50.0 + left_coords[:-1]
    right_coords = 50.0 - np.geomspace(50.0 - r_fine, dx_fine, n_inplane_coarse + 1)[::-1][:-1]
    right_coords = right_coords[::-1]

    x_grid = np.unique(np.concatenate([np.linspace(-50.0, -r_fine, n_inplane_coarse, endpoint=False),
                                      fine_coords,
                                      np.linspace(r_fine, 50.0, n_inplane_coarse + 1)[1:]]))
    y_grid = x_grid.copy()
    nx = len(x_grid)
    ny = len(y_grid)

    print(f"In-plane grid size: {nx} x {ny} = {nx * ny} nodes per layer")

    # Z-coordinates
    # Bottom skin: 2 elements through thickness
    # Core: 6 elements through thickness
    # Top skin: 2 elements through thickness
    z_bot = np.linspace(z_bot_skin_min, z_bot_skin_max, 3)
    z_core = np.linspace(z_core_min, z_core_max, 7)[1:-1]
    z_top = np.linspace(z_top_skin_min, z_top_skin_max, 3)
    z_all = np.concatenate([z_bot, z_core, z_top])
    nz = len(z_all)

    # 1. Create nodes for sandwich panel
    node_id = 1
    grid_node_map = {} # (ix, iy, iz) -> node_id

    for iz, z in enumerate(z_all):
        for iy, y in enumerate(y_grid):
            for ix, x in enumerate(x_grid):
                deck.add_node(node_id, x, y, z)
                grid_node_map[(ix, iy, iz)] = node_id
                node_id += 1

    print(f"Total sandwich nodes: {node_id - 1}")

    # Parts:
    # 1: Bottom Skin (CFRP solid)
    # 2: Honeycomb Core (Solid LAW28)
    # 3: Top Skin (CFRP solid)
    # 4: Rigid Punch (Rigid shell)
    # 5: Rigid Support (Rigid shell)
    deck.parts[1] = "BOTTOM_CFRP_SKIN"
    deck.parts[2] = "HONEYCOMB_CORE"
    deck.parts[3] = "TOP_CFRP_SKIN"
    deck.parts[4] = "RIGID_PUNCH"
    deck.parts[5] = "RIGID_SUPPORT"

    elem_id = 1
    # 2. Add elements
    for iz in range(nz - 1):
        z_mid = 0.5 * (z_all[iz] + z_all[iz+1])
        if z_mid < z_bot_skin_max:
            part_id = 1
        elif z_mid < z_core_max:
            part_id = 2
        else:
            part_id = 3

        for iy in range(ny - 1):
            for ix in range(nx - 1):
                n1 = grid_node_map[(ix, iy, iz)]
                n2 = grid_node_map[(ix+1, iy, iz)]
                n3 = grid_node_map[(ix+1, iy+1, iz)]
                n4 = grid_node_map[(ix, iy+1, iz)]
                n5 = grid_node_map[(ix, iy, iz+1)]
                n6 = grid_node_map[(ix+1, iy, iz+1)]
                n7 = grid_node_map[(ix+1, iy+1, iz+1)]
                n8 = grid_node_map[(ix, iy+1, iz+1)]
                deck.add_brick(elem_id, part_id, [n1, n2, n3, n4, n5, n6, n7, n8])
                elem_id += 1

    print(f"Total sandwich solid elements: {len(deck.bricks)}")

    # 3. Add Rigid Indenter (Punch)
    # Cylinder flat face at z = z_top_skin_max + 0.1 mm
    punch_nodes = []
    z_punch_face = z_top_skin_max + 0.05
    n_theta = 24
    n_r = 6
    r_steps = np.linspace(0.0, r_punch, n_r + 1)
    theta_steps = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)

    center_node_id = node_id
    deck.add_node(center_node_id, 0.0, 0.0, z_punch_face)
    punch_nodes.append(center_node_id)
    node_id += 1

    ring_nodes = []
    for ir in range(1, n_r + 1):
        r = r_steps[ir]
        r_ring = []
        for it, th in enumerate(theta_steps):
            x = r * np.cos(th)
            y = r * np.sin(th)
            deck.add_node(node_id, x, y, z_punch_face)
            punch_nodes.append(node_id)
            r_ring.append(node_id)
            node_id += 1
        ring_nodes.append(r_ring)

    # Shell elements for punch face
    for it in range(n_theta):
        it_next = (it + 1) % n_theta
        # Inner triangle as quad (duplicate node)
        n1 = center_node_id
        n2 = ring_nodes[0][it]
        n3 = ring_nodes[0][it_next]
        deck.add_shell(elem_id, 4, [n1, n2, n3, n3])
        elem_id += 1

    for ir in range(n_r - 1):
        for it in range(n_theta):
            it_next = (it + 1) % n_theta
            n1 = ring_nodes[ir][it]
            n2 = ring_nodes[ir+1][it]
            n3 = ring_nodes[ir+1][it_next]
            n4 = ring_nodes[ir][it_next]
            deck.add_shell(elem_id, 4, [n1, n2, n3, n4])
            elem_id += 1

    print(f"Punch shell elements: {len(deck.shells)}")

    # 4. Materials & Properties Cards
    # Property for solid elements (HEPH 8-node brick)
    deck.properties.append(
"""/PROP/TYPE14/1
SOLID_CFRP_PROP
#   Isolid     Ismstr      Icpre      Itet4     
         1          1          0          0
"""
    )
    deck.properties.append(
"""/PROP/TYPE14/2
SOLID_HONEYCOMB_PROP
#   Isolid     Ismstr      Icpre      Itet4     
         1          1          0          0
"""
    )
    deck.properties.append(
"""/PROP/TYPE14/3
SOLID_CFRP_PROP_TOP
#   Isolid     Ismstr      Icpre      Itet4     
         1          1          0          0
"""
    )
    deck.properties.append(
"""/PROP/TYPE1/4
PUNCH_SHELL_PROP
#   Ishell      Ismstr     Ish3n
         1           1         1
#       Thick
         1.0
"""
    )

    # Materials
    # CFRP Material LAW25 (Orthotropic Fabric with Tsai-Wu / Chang-Chang failure)
    deck.materials.append(
"""/MAT/LAW25/1
CFRP_T700_TWILL_LAW25
#   RHO_I (Mg/mm3)
  1.500000E-09
#          E11             E22            NU12             G12             G23             G31
  56000.000000    56500.000000        0.050000     2990.000000     2800.000000     2800.000000
#           Xt              Yt              Xc              Yc               S
    925.000000     1026.000000      559.000000      599.000000      104.000000
#        E_PL1           E_PL2           Sigma1          Sigma2        eps_max
    500.000000      500.000000      850.000000      950.000000        0.050000
"""
    )

    # Honeycomb Material LAW28 (Orthotropic Crushable Honeycomb)
    # 5052-1/8-0.0015-6.1: E33 = 1654.7 MPa, G13 = 675.7 MPa, G23 = 282.7 MPa, sig_crush = 3.10 MPa, sig_bare = 6.0 MPa
    deck.materials.append(
"""/MAT/LAW28/2
AL_HONEYCOMB_5052_6_1_LAW28
#   RHO_I (Mg/mm3)
  9.760000E-11
#          E11             E22             E33            NU12            NU23            NU31
      5.000000        5.000000     1654.700000        0.010000        0.010000        0.010000
#          G12             G23             G31
      2.000000      282.700000      675.700000
#      sig_L33       sig_crush          sig_13          sig_23
      6.000000        3.100000        3.480000        2.210000
"""
    )

    deck.materials.append(
"""/MAT/LAW25/3
CFRP_T700_TWILL_LAW25_TOP
#   RHO_I (Mg/mm3)
  1.500000E-09
#          E11             E22            NU12             G12             G23             G31
  56000.000000    56500.000000        0.050000     2990.000000     2800.000000     2800.000000
#           Xt              Yt              Xc              Yc               S
    925.000000     1026.000000      559.000000      599.000000      104.000000
#        E_PL1           E_PL2           Sigma1          Sigma2        eps_max
    500.000000      500.000000      850.000000      950.000000        0.050000
"""
    )

    # Rigid Steel Punch Material (LAW1 Elastic with high modulus or rigid body)
    deck.materials.append(
"""/MAT/LAW1/4
RIGID_STEEL_PUNCH
#   RHO_I (Mg/mm3)
  7.850000E-09
#            E              NU
 210000.000000        0.300000
"""
    )

    # 5. Boundary Conditions & Contacts
    # Rigid body definition for punch nodes
    deck.bcs.append(
f"""/RBODY/1
RIGID_PUNCH_BODY
#      Node_m   Icoor
  {center_node_id:10d}       0
# Tra_X  Tra_Y  Tra_Z  Rot_X  Rot_Y  Rot_Z
      1      1      0      1      1      1
"""
    )

    # Impose constant downward velocity on center punch node
    deck.bcs.append(
f"""/IMPVLOC/1
PUNCH_VELOCITY_Z
#      Node_id     Dir      Scale
  {center_node_id:10d}       Z {-v_punch:12.4f}
#      Fct_idT
             0
"""
    )

    # Support Boundary Condition:
    # Constrain bottom skin nodes where r >= aperture_radius (15 mm) in Z
    deck.bcs.append(
"""/BCS/1
SUPPORT_APERTURE_CLAMP
# Tra_X  Tra_Y  Tra_Z  Rot_X  Rot_Y  Rot_Z
      0      0      1      0      0      0
"""
    )

    # Contact: TYPE 7 Surface-to-Surface contact with friction
    deck.contacts.append(
"""/INTER/TYPE7/1
PUNCH_TO_TOPSKIN_CONTACT
#      Slav_id     Mast_id
             3           4
#        Fric_coef
          0.250000
#   Istf      Igap      Idel
       4         2         1
"""
    )

    return deck, {
        "nx": nx, "ny": ny, "nz": nz,
        "n_nodes": len(deck.nodes),
        "n_bricks": len(deck.bricks),
        "n_shells": len(deck.shells),
        "t_end": t_end,
        "v_punch": v_punch
    }

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parents[2]
    starter_path = base_dir / 'models' / 'phase1_homogenized' / 'starter' / 'PUNCTURE_HOMOG_0000.rad'
    engine_path = base_dir / 'models' / 'phase1_homogenized' / 'engine' / 'PUNCTURE_HOMOG_0001.rad'

    print("Generating Phase 1 Homogenized Sandwich Puncture FE Model...")
    deck, stats = build_phase1_deck()
    deck.write_starter(starter_path)
    deck.write_engine(engine_path, t_stop=stats['t_end'])

    print(f"Starter deck written: {starter_path} ({starter_path.stat().st_size / 1024:.1f} KB)")
    print(f"Engine deck written:  {engine_path} ({engine_path.stat().st_size / 1024:.1f} KB)")
    print("Model generation completed successfully.")
