"""
Phase 2: Meso-scale Hybrid Model Generator
Combines explicit hexagonal aluminium honeycomb cell walls (shell elements)
in the puncture zone with 3D solid CFRP face sheets and far-field core.
"""

from pathlib import Path
import numpy as np
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from radioss_writer import RadiossDeck
from mesoscale_honeycomb_generator import generate_hex_grid, discretize_cell_walls

def build_phase2_deck(
    panel_l: float = 100.0,
    panel_w: float = 100.0,
    r_meso: float = 18.0,
    cell_size: float = 3.175, # 1/8 inch
    n_inplane_far: int = 35,
    punch_dia: float = 25.0,
    aperture_dia: float = 30.0,
    v_punch: float = 1000.0,
    t_end: float = 0.016,
) -> tuple[RadiossDeck, dict]:
    deck = RadiossDeck(title="PUNCTURE_MESO")

    t_ply = 0.333
    n_plies = 7
    t_skin = n_plies * t_ply # 2.331 mm
    h_core = 15.0 # mm
    r_punch = punch_dia / 2.0
    r_aper = aperture_dia / 2.0

    z_bot_min = 0.0
    z_bot_max = t_skin
    z_core_min = z_bot_max
    z_core_max = z_core_min + h_core
    z_top_min = z_core_max
    z_top_max = z_top_min + t_skin

    # Parts:
    # 1: Bottom Skin (CFRP 3D solid)
    # 2: Outer Core (Homogenized solid)
    # 3: Top Skin (CFRP 3D solid)
    # 4: Rigid Punch (Rigid shell)
    # 21: Meso Honeycomb Single Foil (Shell t=0.0381 mm)
    # 22: Meso Honeycomb Double Foil (Shell t=0.0762 mm)
    deck.parts[1]  = ("BOTTOM_CFRP_SKIN", 1, 1)
    deck.parts[2]  = ("OUTER_HONEYCOMB",  2, 2)
    deck.parts[3]  = ("TOP_CFRP_SKIN",    3, 3)
    deck.parts[4]  = ("RIGID_PUNCH",      4, 4)
    deck.parts[21] = ("HEX_FOIL_SINGLE",  21, 21)
    deck.parts[22] = ("HEX_FOIL_DOUBLE",  22, 22)

    # 1. Generate Meso-Scale Honeycomb Cells in Puncture Zone
    print(f"Generating meso-scale hexagonal cell grid (r <= {r_meso} mm)...")
    cells = generate_hex_grid(r_patch=r_meso, cell_size=cell_size)
    hex_nodes, hex_shells, next_nid, next_eid = discretize_cell_walls(
        cells, z_min=z_core_min, z_max=z_core_max, n_z_elem=5, n_edge_elem=2,
        node_start_id=1, elem_start_id=1, part_single_foil=21, part_double_foil=22
    )

    for nid, (x, y, z) in hex_nodes.items():
        deck.add_node(nid, x, y, z)

    for eid, pid, nids in hex_shells:
        deck.add_shell(eid, pid, nids)

    print(f"Added {len(hex_nodes)} meso-scale nodes and {len(hex_shells)} shell elements.")

    # 2. Generate Top and Bottom CFRP Skins + Outer Core
    x_grid = np.linspace(-50.0, 50.0, n_inplane_far + 1)
    y_grid = x_grid.copy()
    nx, ny = len(x_grid), len(y_grid)

    z_bot = np.linspace(z_bot_min, z_bot_max, 3)
    z_outer_core = np.linspace(z_core_min, z_core_max, 4)[1:-1]
    z_top = np.linspace(z_top_min, z_top_max, 3)
    z_all = np.concatenate([z_bot, z_outer_core, z_top])
    nz = len(z_all)

    node_map = {}
    bot_aperture_nodes = []
    node_id = next_nid

    for iz, z in enumerate(z_all):
        for iy, y in enumerate(y_grid):
            for ix, x in enumerate(x_grid):
                deck.add_node(node_id, x, y, z)
                node_map[(ix, iy, iz)] = node_id
                if iz == 0 and (x**2 + y**2 >= r_aper**2):
                    bot_aperture_nodes.append(node_id)
                node_id += 1

    elem_id = next_eid
    for iz in range(nz - 1):
        z_mid = 0.5 * (z_all[iz] + z_all[iz+1])
        is_core_layer = (z_mid >= z_core_min and z_mid <= z_core_max)

        for iy in range(ny - 1):
            for ix in range(nx - 1):
                xc = 0.5 * (x_grid[ix] + x_grid[ix+1])
                yc = 0.5 * (y_grid[iy] + y_grid[iy+1])
                rc = np.sqrt(xc**2 + yc**2)

                # Omit solid bricks inside meso patch for core layer
                if is_core_layer and rc <= r_meso:
                    continue

                if z_mid < z_bot_max:
                    part_id = 1
                elif z_mid > z_top_min:
                    part_id = 3
                else:
                    part_id = 2

                n1 = node_map[(ix, iy, iz)]
                n2 = node_map[(ix+1, iy, iz)]
                n3 = node_map[(ix+1, iy+1, iz)]
                n4 = node_map[(ix, iy+1, iz)]
                n5 = node_map[(ix, iy, iz+1)]
                n6 = node_map[(ix+1, iy, iz+1)]
                n7 = node_map[(ix+1, iy+1, iz+1)]
                n8 = node_map[(ix, iy+1, iz+1)]
                deck.add_brick(elem_id, part_id, [n1, n2, n3, n4, n5, n6, n7, n8])
                elem_id += 1

    # 3. Add Rigid Indenter
    # Position punch mid-surface at z_top_max + 1.1 mm (punch shell thickness = 2.0 mm -> outer bottom face at +0.1 mm)
    z_punch_face = z_top_max + 1.10
    n_theta = 24
    n_r = 5
    r_steps = np.linspace(0.0, r_punch, n_r + 1)
    theta_steps = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)

    center_node_id = node_id
    deck.add_node(center_node_id, 0.0, 0.0, z_punch_face)
    punch_nodes = [center_node_id]
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

    # 4. Properties
    for pid in [1, 2, 3]:
        deck.properties.append(
f"""/PROP/TYPE14/{pid}/0
SOLID_PROP_{pid}
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

    deck.properties.append(
"""/PROP/TYPE1/21/0
AL_FOIL_SINGLE
2          2          2          0          0        0.0
0.0        0.0        0.0        0.0        0.0
5     0.038100        1.0        0          2"""
    )

    deck.properties.append(
"""/PROP/TYPE1/22/0
AL_FOIL_DOUBLE
2          2          2          0          0        0.0
0.0        0.0        0.0        0.0        0.0
5     0.076200        1.0        0          2"""
    )

    # 5. Materials
    for pid in [1, 3]:
        deck.materials.append(
f"""/MAT/LAW1/{pid}
CFRP_SKIN_LAW1_{pid}
1.500000E-09
56000.000000000000000.050000000000000000"""
        )

    deck.materials.append(
"""/MAT/LAW1/2
OUTER_CORE_LAW1
9.760000E-11
1654.7000000000000000.010000000000000000"""
    )

    deck.materials.append(
"""/MAT/LAW1/4
RIGID_STEEL_PUNCH
7.850000E-09
210000.00000000000000.300000000000000000"""
    )

    for pid in [21, 22]:
        deck.materials.append(
f"""/MAT/LAW1/{pid}
AL_5052_ALLOY_FOIL_{pid}
2.680000E-09
70000.000000000000000.330000000000000000"""
        )

    # 6. Surfaces & Contact
    # Master surface: Punch shells (Part 4)
    # Slave nodes: Sandwich nodes in puncture interaction zone (r <= 28 mm)
    candidate_contact_nodes = [nid for nid, node in deck.nodes.items() if nid < center_node_id and (node.x**2 + node.y**2)**0.5 <= 28.0]
    contact_nodes_str = ""
    for i, nid in enumerate(candidate_contact_nodes):
        contact_nodes_str += f"{nid:10d}"
        if (i + 1) % 10 == 0 or (i + 1) == len(candidate_contact_nodes):
            contact_nodes_str += "\n"

    deck.bcs.append(
f"""/GRNOD/NODE/10/0
SANDWICH_CONTACT_SLAVE_NODES
{contact_nodes_str.rstrip()}"""
    )

    deck.surfaces.append(
"""/SURF/PART/1
PUNCH_SURF
4"""
    )
    deck.surfaces.append(
"""/SURF/PART/EXT/2
SANDWICH_SOLID_SURF
1         2         3"""
    )

    deck.contacts.append(
f"""/INTER/TYPE7/1
PUNCH_TO_PANEL
        10         1         4                    1         0         0         0         0
{1.0:20.6f}{0.0:20.6f}
{1000.0:20.6f}{100000.0:20.6f}
{1.0:20.6f}{0.25:20.6f}{0.05:20.6f}{0.0:20.6f}{0.0:20.6f}
       000                    0{0.05:20.6f}{0.0:20.6f}{0.0:20.6f}
         0         0{0.0:20.6f}         2"""
    )

    # 7. Rigid Body for Punch
    p_str = ""
    for i, nid in enumerate(punch_nodes):
        p_str += f"{nid:10d}"
        if (i + 1) % 10 == 0 or (i + 1) == len(punch_nodes):
            p_str += "\n"

    deck.bcs.append(
f"""/GRNOD/NODE/1/0
PUNCH_SLAVE_NODES
{p_str.rstrip()}
/RBODY/1/0
RIGID_PUNCH
{center_node_id:10d}         0         0         2     5.000E-04         1         0         1         0
0.0       0.0       0.0
0.0       0.0       0.0"""
    )

    # 8. Boundary conditions (Aperture support clamp)
    supp_str = ""
    for i, nid in enumerate(bot_aperture_nodes):
        supp_str += f"{nid:10d}"
        if (i + 1) % 10 == 0 or (i + 1) == len(bot_aperture_nodes):
            supp_str += "\n"

    deck.bcs.append(
f"""/GRNOD/NODE/2/0
SUPPORT_CLAMP_NODES
{supp_str.rstrip()}
/BCS/1
SUPPORT_APERTURE_CLAMP
    111111         0         2"""
    )

    # 9. Imposed velocity
    deck.bcs.append(
f"""/FUNCT/1
RAMP_VELOCITY
          0.00000   {-v_punch:14.5f}
          1.00000   {-v_punch:14.5f}
/GRNOD/NODE/3/0
PUNCH_MASTER_NODE_SET
{center_node_id:10d}
/IMPVEL/1
IMPOSED_PUNCH_VELOCITY
         1         Z         0         0         3         0         0
{1.0:20.6f}{1.0:20.6f}{0.0:20.6f}{0.0:20.6f}"""
    )

    # 10. Time Histories
    deck.time_histories.append(
f"""/TH/NODE/1
PUNCH_DISP
DZ
{center_node_id:10d}
/TH/RBODY/2
PUNCH_FORCE
FZ
1"""
    )

    total_bricks = sum(len(b) for b in deck.bricks_by_part.values())
    total_shells = sum(len(s) for s in deck.shells_by_part.values())
    print(f"Phase 2 Total Nodes: {len(deck.nodes)}")
    print(f"Phase 2 Total Solids: {total_bricks}")
    print(f"Phase 2 Total Shells: {total_shells}")

    return deck, {
        "n_nodes": len(deck.nodes),
        "n_bricks": total_bricks,
        "n_shells": total_shells,
        "t_end": t_end,
        "v_punch": v_punch
    }

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parents[2]
    starter_path = base_dir / 'models' / 'phase2_mesoscale' / 'starter' / 'PUNCTURE_MESO_0000.rad'
    engine_path = base_dir / 'models' / 'phase2_mesoscale' / 'engine' / 'PUNCTURE_MESO_0001.rad'

    print("Generating Phase 2 Meso-scale Hybrid Sandwich FE Model...")
    deck, stats = build_phase2_deck()
    deck.write_starter(starter_path)
    deck.write_engine(engine_path, t_stop=stats['t_end'])

    print(f"Phase 2 Starter deck: {starter_path} ({starter_path.stat().st_size / 1024:.1f} KB)")
    print(f"Phase 2 Engine deck:  {engine_path} ({engine_path.stat().st_size / 1024:.1f} KB)")
    print("Phase 2 Model generation complete.")
