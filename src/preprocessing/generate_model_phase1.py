"""
Phase 1: Homogenized Core Model Generator
Generates full 3D OpenCourant input decks (Starter _0000.rad and Engine _0001.rad)
for the CFRP / Aluminium Honeycomb Sandwich Puncture Simulation.
"""

from pathlib import Path
import numpy as np
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from radioss_writer import RadiossDeck

def build_phase1_deck(
    panel_l: float = 100.0,
    panel_w: float = 100.0,
    n_inplane_fine: int = 30,
    n_inplane_coarse: int = 10,
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
    deck = RadiossDeck(title="PUNCTURE_HOMOG")

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

    # In-plane mesh: Cartesian grid centered at (0,0)
    fine_coords = np.linspace(-r_fine, r_fine, n_inplane_fine + 1)
    x_grid = np.unique(np.concatenate([
        np.linspace(-50.0, -r_fine, n_inplane_coarse, endpoint=False),
        fine_coords,
        np.linspace(r_fine, 50.0, n_inplane_coarse + 1)[1:]
    ]))
    y_grid = x_grid.copy()
    nx = len(x_grid)
    ny = len(y_grid)

    print(f"In-plane grid size: {nx} x {ny} = {nx * ny} nodes per layer")

    # Z-discretization
    z_bot = np.linspace(z_bot_skin_min, z_bot_skin_max, 3)
    z_core = np.linspace(z_core_min, z_core_max, 5)[1:-1]
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
    # 2: Honeycomb Core (Solid crushable)
    # 3: Top Skin (CFRP solid)
    # 4: Rigid Punch (Rigid shell)
    deck.parts[1] = ("BOTTOM_CFRP_SKIN", 1, 1)
    deck.parts[2] = ("HONEYCOMB_CORE",   2, 2)
    deck.parts[3] = ("TOP_CFRP_SKIN",    3, 3)
    deck.parts[4] = ("RIGID_PUNCH",      4, 4)

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

    total_bricks = sum(len(b) for b in deck.bricks_by_part.values())
    print(f"Total sandwich solid elements: {total_bricks}")

    # 3. Add Rigid Indenter (Punch)
    punch_nodes = []
    z_punch_face = z_top_skin_max + 0.05
    n_theta = 24
    n_r = 5
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

    total_shells = sum(len(s) for s in deck.shells_by_part.values())
    print(f"Punch shell elements: {total_shells}")

    # 4. Materials & Properties Cards
    # Solid property for CFRP skins and core (TYPE14)
    deck.properties.append(
"""/PROP/TYPE14/1/0
SOLID_CFRP_BOTTOM
1          4          0          0          0          0          0          0        0.0
0.1        0.1        1.0        0.0        0.0
0.0        0.0        0.0        0.0        0.0
0          0          0"""
    )
    deck.properties.append(
"""/PROP/TYPE14/2/0
SOLID_HONEYCOMB
1          4          0          0          0          0          0          0        0.0
0.1        0.1        1.0        0.0        0.0
0.0        0.0        0.0        0.0        0.0
0          0          0"""
    )
    deck.properties.append(
"""/PROP/TYPE14/3/0
SOLID_CFRP_TOP
1          4          0          0          0          0          0          0        0.0
0.1        0.1        1.0        0.0        0.0
0.0        0.0        0.0        0.0        0.0
0          0          0"""
    )
    deck.properties.append(
"""/PROP/TYPE1/4/0
PUNCH_SHELL
2          2          2          0          0        0.0
0.0        0.0        0.0        0.0        0.0
5          2.0        1.0        0          2"""
    )

    # Materials
    # Mat 1: Bottom CFRP (Law 1 elastic baseline, calib to Law 25)
    deck.materials.append(
"""/MAT/LAW1/1
CFRP_BOTTOM_LAW1
1.500000E-09
56000.000000000000000.050000000000000000"""
    )
    # Mat 2: Honeycomb core (Law 1 equivalent crushable modulus, calib to Law 36/28)
    deck.materials.append(
"""/MAT/LAW1/2
HONEYCOMB_CORE_LAW1
9.760000E-11
1654.7000000000000000.010000000000000000"""
    )
    # Mat 3: Top CFRP
    deck.materials.append(
"""/MAT/LAW1/3
CFRP_TOP_LAW1
1.500000E-09
56000.000000000000000.050000000000000000"""
    )
    # Mat 4: Steel Punch
    deck.materials.append(
"""/MAT/LAW1/4
RIGID_STEEL_PUNCH
7.850000E-09
210000.00000000000000.300000000000000000"""
    )

    return deck, {
        "nx": nx, "ny": ny, "nz": nz,
        "n_nodes": len(deck.nodes),
        "n_bricks": total_bricks,
        "n_shells": total_shells,
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
