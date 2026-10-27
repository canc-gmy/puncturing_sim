"""
Phase 2: Meso-Scale Honeycomb Core Sandwich Puncture Model Generator (v2.2)
Features:
- Quarter-symmetric polar in-plane mesh (x >= 0, y >= 0, 50x50 mm)
- Explicit 3D hexagonal aluminium honeycomb cell walls (shell elements, parts 21 & 22)
  in the central puncture zone (r <= 18.0 mm) with Johnson-Cook plasticity (/MAT/LAW2)
- Homogenized crushable honeycomb core (/MAT/LAW28 + /PROP/TYPE6) in the outer zone (r > 18.0 mm)
- 7 distinct orthotropic solid plies per CFRP skin ([0/45/0/45/0/45/0]) with /PROP/TYPE6
- Progressive composite damage model /MAT/LAW25 (Chang-Chang) + /FAIL/CHANG
- Dedicated edge-to-surface contact (/INTER/TYPE19) between composite skins and foil shell edges
  with Iedge=1 and INACTIV=1 to prevent horizontal mesh blow-up and ensure purely vertical force transmission
- Honeycomb foil self-contact (/INTER/TYPE7/4) with INACTIV=1 for realistic cell wall folding
- Rigid cylindrical steel punch (R=12.5 mm quarter disc) with /INTER/TYPE7 penalty contact
- Symmetric boundary conditions on x=0 (100 011) and y=0 (010 101) across skins, solids, and foils
- Ultra-low inertia quasi-static loading: 50 mm/s with 10 ms smooth sinusoidal ramp (t_stop = 0.324 s)
- 81 animation states (0.20 mm displacement per frame over 16.2 mm stroke)
"""

from pathlib import Path
import numpy as np
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from polar_mesh_quarter import generate_quarter_inplane_mesh
from mesoscale_honeycomb_quarter import generate_hex_grid, discretize_quarter_cell_walls
from radioss_writer import RadiossDeck

def format_node_set(node_list: list[int]) -> str:
    lines = []
    current_line = []
    for nid in node_list:
        current_line.append(f"{nid:10d}")
        if len(current_line) == 10:
            lines.append("".join(current_line))
            current_line = []
    if current_line:
        lines.append("".join(current_line))
    return "\n".join(lines)

def build_phase2_v2_deck(
    panel_l: float = 50.0,
    panel_w: float = 50.0,
    r_meso: float = 18.0,
    cell_size: float = 3.175, # 1/8 inch
    punch_dia: float = 25.0,
    aperture_dia: float = 30.0,
    v_punch: float = 1000.0,  # mm/s = 1.0 m/s explicit rapid calibration
    t_end: float = 0.0162,    # 16.2 ms -> 16.2 mm displacement at 1000 mm/s
    nc_inplane: int = 8,
    n_core_layers: int = 10,
) -> tuple[RadiossDeck, dict]:
    deck = RadiossDeck(title="PUNCTURE_MESO")

    # 1. Geometry & Layup
    t_ply = 0.333          # mm per ply
    n_plies = 7
    t_skin = n_plies * t_ply # 2.331 mm
    h_core = 15.0          # mm
    total_thickness = 2.0 * t_skin + h_core # 19.662 mm

    z_bot_min = 0.0
    z_bot_max = t_skin # 2.331 mm
    z_core_min = z_bot_max # 2.331 mm
    z_core_max = z_core_min + h_core # 17.331 mm
    z_top_min = z_core_max # 17.331 mm
    z_top_max = z_top_min + t_skin # 19.662 mm

    ply_angles = [0.0, 45.0, 0.0, 45.0, 0.0, 45.0, 0.0]

    # Z-coordinates of layer interfaces for sandwich solids
    z_layers = []
    # Bottom skin: 7 layers
    for i in range(n_plies + 1):
        z_layers.append(i * t_ply)
    
    # Core: n_core_layers layers
    z_core_start = z_layers[-1]
    dz_core = h_core / n_core_layers
    for i in range(1, n_core_layers + 1):
        z_layers.append(z_core_start + i * dz_core)

    # Top skin: 7 layers
    z_top_start = z_layers[-1]
    for i in range(1, n_plies + 1):
        z_layers.append(z_top_start + i * t_ply)

    z_layers = np.array(z_layers)
    n_z_layers = len(z_layers) - 1

    # 2. In-Plane Quarter 2D Mesh for Composite Skins & Outer Core
    nodes_2d, quads_2d, _ = generate_quarter_inplane_mesh(nc=nc_inplane, r0=4.0)
    n_nodes_2d = len(nodes_2d)
    r_nodes_2d = np.sqrt(nodes_2d[:, 0]**2 + nodes_2d[:, 1]**2)

    # 3. Discretize Meso-scale Honeycomb Foil Walls in Q1 Puncture Zone
    print(f"Generating explicit honeycomb cells in Q1 patch (r <= {r_meso} mm)...")
    cells = generate_hex_grid(r_patch=r_meso, cell_size=cell_size)
    hex_nodes, hex_shells, hex_sym_x, hex_sym_y, hex_bot_nodes, hex_top_nodes, next_nid, next_eid = discretize_quarter_cell_walls(
        cells, z_min=z_core_min, z_max=z_core_max, n_z_elem=6, n_edge_elem=1,
        node_start_id=1, elem_start_id=1, part_single_foil=21, part_double_foil=22
    )

    candidate_contact_nodes = []

    for nid, (x, y, z) in hex_nodes.items():
        deck.add_node(nid, x, y, z)
        if np.sqrt(x**2 + y**2) <= 18.0:
            candidate_contact_nodes.append(nid)

    for eid, pid, nids in hex_shells:
        deck.add_shell(eid, pid, nids)

    print(f"Added {len(hex_nodes)} meso-scale nodes and {len(hex_shells)} foil shell elements.")
    print(f"Honeycomb bottom nodes: {len(hex_bot_nodes)}, top: {len(hex_top_nodes)}")

    # 4. Extrude 3D Sandwich Mesh (Skins across full panel, Core only for r > r_meso)
    node_id = next_nid
    elem_id = next_eid
    node_map_3d = {}
    bot_aperture_clamped_nodes = []
    solid_sym_x_nodes = []
    solid_sym_y_nodes = []

    for iz, z in enumerate(z_layers):
        for in2d in range(n_nodes_2d):
            x, y = nodes_2d[in2d]
            deck.add_node(node_id, x, y, z)
            node_map_3d[(in2d, iz)] = node_id

            # Clamping boundary: bottom plane (iz == 0) and r >= 14.999 mm (outside aperture)
            if iz == 0 and r_nodes_2d[in2d] >= 14.999:
                bot_aperture_clamped_nodes.append(node_id)

            # Symmetry X plane (x = 0)
            if abs(x) < 1e-5:
                solid_sym_x_nodes.append(node_id)

            # Symmetry Y plane (y = 0)
            if abs(y) < 1e-5:
                solid_sym_y_nodes.append(node_id)

            # Punch contact candidates: top skin outer face nodes with r <= 18.0 mm
            if iz == (len(z_layers) - 1) and r_nodes_2d[in2d] <= 18.0:
                candidate_contact_nodes.append(node_id)

            node_id += 1

    # 5. Define Solid Elements
    for iz in range(n_z_layers):
        is_bottom_skin = (iz < n_plies)
        is_top_skin = (iz >= n_plies + n_core_layers)
        is_core = not (is_bottom_skin or is_top_skin)

        if is_bottom_skin:
            part_id = 101 + iz
        elif is_top_skin:
            part_id = 108 + (iz - (n_plies + n_core_layers))
        else:
            part_id = 2 # Homogenized core

        for q in quads_2d:
            n1_2d, n2_2d, n3_2d, n4_2d = q
            # For core: only create solid elements outside the meso patch (r > r_meso)
            if is_core:
                r_quad_center = np.mean([r_nodes_2d[n] for n in q])
                if r_quad_center <= r_meso:
                    continue # Meso explicit shells replace solids here

            n1 = node_map_3d[(n1_2d, iz)]
            n2 = node_map_3d[(n2_2d, iz)]
            n3 = node_map_3d[(n3_2d, iz)]
            n4 = node_map_3d[(n4_2d, iz)]
            n5 = node_map_3d[(n1_2d, iz + 1)]
            n6 = node_map_3d[(n2_2d, iz + 1)]
            n7 = node_map_3d[(n3_2d, iz + 1)]
            n8 = node_map_3d[(n4_2d, iz + 1)]
            deck.add_brick(elem_id, part_id, [n1, n2, n3, n4, n5, n6, n7, n8])
            elem_id += 1

    total_bricks = sum(len(b) for b in deck.bricks_by_part.values())
    print(f"Generated {total_bricks} solid brick elements (skins + outer core).")

    # 6. Punch Geometry (Rigid Quarter Cylindrical Shell Disc, R=12.5mm)
    z_punch_face = z_layers[-1] + 0.50 + 0.20 # 20.362 mm (0.20 mm initial clearance)
    punch_center_id = node_id
    deck.add_node(punch_center_id, 0.0, 0.0, z_punch_face)
    node_id += 1

    punch_nodes = [punch_center_id]
    punch_node_map_2d = {}

    punch_nodes_2d_idx = [i for i, r in enumerate(r_nodes_2d) if r <= 12.501]
    for in2d in punch_nodes_2d_idx:
        x, y = nodes_2d[in2d]
        deck.add_node(node_id, x, y, z_punch_face)
        punch_node_map_2d[in2d] = node_id
        punch_nodes.append(node_id)
        node_id += 1

    for q in quads_2d:
        n1_2d, n2_2d, n3_2d, n4_2d = q
        if all(nid in punch_node_map_2d for nid in [n1_2d, n2_2d, n3_2d, n4_2d]):
            p1 = punch_node_map_2d[n1_2d]
            p2 = punch_node_map_2d[n2_2d]
            p3 = punch_node_map_2d[n3_2d]
            p4 = punch_node_map_2d[n4_2d]
            # Normal facing down towards top skin (-Z)
            deck.add_shell(elem_id, 4, [p1, p4, p3, p2])
            elem_id += 1

    total_shells = sum(len(s) for s in deck.shells_by_part.values())
    print(f"Generated rigid quarter punch with {len(punch_nodes)} nodes and {len(deck.shells_by_part[4])} shells.")
    print(f"Total shells across model: {total_shells}")

    # 7. Define Parts
    # Bottom skin plies (101..107)
    for p_idx in range(n_plies):
        part_id = 101 + p_idx
        prop_id = 101 + p_idx
        mat_id = 1
        deck.parts[part_id] = (f"BOT_CFRP_PLY_{p_idx+1}", prop_id, mat_id)

    # Core part (2)
    deck.parts[2] = ("HONEYCOMB_CORE", 2, 2)

    # Top skin plies (108..114)
    for p_idx in range(n_plies):
        part_id = 108 + p_idx
        prop_id = 108 + p_idx
        mat_id = 1
        deck.parts[part_id] = (f"TOP_CFRP_PLY_{p_idx+1}", prop_id, mat_id)

    # Honeycomb foil shells: single (21) and double (22)
    deck.parts[21] = ("HEX_FOIL_SINGLE", 21, 21)
    deck.parts[22] = ("HEX_FOIL_DOUBLE", 22, 21)

    # Punch part (4)
    deck.parts[4] = ("RIGID_STEEL_PUNCH", 4, 4)

    # 8. Properties Setup
    # Properties 101..107 (Bottom skin plies)
    for p_idx in range(n_plies):
        prop_id = 101 + p_idx
        phi = ply_angles[p_idx]
        deck.properties.append(
f"""/PROP/TYPE6/{prop_id}/0
CFRP_PLY_{p_idx+1}_PROP
         1         4                   0         0         0         0         2            0.000000
                 0.1                 0.1                 0.1
                 0.0                 0.0                 0.0         0         1         0
{phi:20.6f}            0.000000            0.000000            0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         0         0         0"""
        )

    # Property 2 (Outer Core Solid)
    deck.properties.append(
"""/PROP/TYPE6/2/0
HONEYCOMB_CORE_PROP
         1         4                   0         0         0         0         2            0.000000
                 0.1                 0.1                 0.1
                 0.0                 0.0                 0.0         0         1         0
            0.000000            0.000000            0.000000            0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         0         0         0"""
    )

    # Properties 108..114 (Top skin plies)
    for p_idx in range(n_plies):
        prop_id = 108 + p_idx
        phi = ply_angles[p_idx]
        deck.properties.append(
f"""/PROP/TYPE6/{prop_id}/0
CFRP_TOP_PLY_{p_idx+1}_PROP
         1         4                   0         0         0         0         2            0.000000
                 0.1                 0.1                 0.1
                 0.0                 0.0                 0.0         0         1         0
{phi:20.6f}            0.000000            0.000000            0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         0         0         0"""
        )

    # Honeycomb Single Foil Shell Property (21): t = 0.025 mm
    deck.properties.append(
"""/PROP/TYPE1/21/0
HEX_SINGLE_FOIL_PROP
         1         2         2         0         0                      0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         1                      0.025000            0.833333                   0         0         0"""
    )

    # Honeycomb Double Foil Shell Property (22): t = 0.050 mm
    deck.properties.append(
"""/PROP/TYPE1/22/0
HEX_DOUBLE_FOIL_PROP
         1         2         2         0         0                      0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         1                      0.050000            0.833333                   0         0         0"""
    )

    # Rigid Punch Shell Property (4)
    deck.properties.append(
"""/PROP/TYPE1/4/0
PUNCH_RIGID_SHELL_PROP
         1         2         2         0         0                      0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         1                      1.000000            0.833333                   0         0         0"""
    )

    # 9. Materials Setup
    # Mat 1: CFRP Orthotropic with Chang-Chang failure
    deck.materials.append(
"""/MAT/LAW25/1
CFRP_T700_TWILL
        1.500000E-09
        56000.000000        56000.000000            0.050000         0          10000.000000
         2990.000000         2990.000000         2990.000000            0.000000            0.000000
            0.000000            0.000000            0.000000            0.000000            0.990000
            0.000000            0.000000         0            0.000000
            1.000000            1.000000          925.000000
          925.000000          925.000000          559.000000          559.000000            1.000000
          104.000000          104.000000            0.000000            0.000000         0
            0.000000            0.000000            0.000000
         0            0.000000
/FAIL/CHANG/1
          925.000000          925.000000          104.000000          559.000000          559.000000
            1.000000         1.00000E-06         1         1            0.000000"""
    )

    # Mat 2: Crushable Honeycomb Core for outer region (/MAT/LAW28)
    deck.materials.append(
"""/FUNCT/28
HONEYCOMB_CRUSH_CURVE
                 0.0                 4.6
                 0.7                 4.6
                 0.8                30.0
                 0.9               100.0
/MAT/LAW28/2
HONEYCOMB_CORE_LAW28
        9.760000E-11
                10.0                10.0              1654.7
                10.0               140.0               280.0
         0         0        28         1                 1.0                 1.0                 1.0
                 0.0                 0.0                 0.0
         0         0         0         1                 1.0                 1.0                 1.0
                 0.0                 0.0                 0.0"""
    )

    # Mat 21: Aluminium 5052 Foil (Johnson-Cook Plasticity /MAT/LAW2)
    deck.materials.append(
"""/MAT/LAW2/21
AL_5052_FOIL
        2.680000E-09
        70000.000000            0.330000
          255.000000          410.000000            0.250000            0.150000
            0.000000            1.000000            0.000000            0.000000         0            0.000000
            0.000000            0.000000         0            0.000000"""
    )

    # Mat 4: Rigid Steel Punch (/MAT/LAW1)
    deck.materials.append(
"""/MAT/LAW1/4
RIGID_STEEL_PUNCH
        7.850000E-09
       210000.000000            0.300000"""
    )

    # 10. Surfaces & Interfaces
    # Surface 1: Punch shells (Part 4)
    deck.surfaces.append(
"""/SURF/PART/1
PUNCH_SURFACE
4"""
    )

    # Surface 20: Foil shells (Parts 21 & 22)
    deck.surfaces.append(
"""/SURF/PART/20
HEX_FOIL_SURFACE
        21        22"""
    )

    # Surface 10: Top skin inner face (external surface of lowest top ply Part 108)
    deck.surfaces.append(
"""/SURF/PART/EXT/10
TOP_SKIN_INNER_SURF
       108"""
    )

    # Surface 11: Bottom skin inner face (external surface of highest bottom ply Part 107)
    deck.surfaces.append(
"""/SURF/PART/EXT/11
BOT_SKIN_INNER_SURF
       107"""
    )

    # Contact 1: Punch to Top Skin (/INTER/TYPE7/1)
    contact_nodes_str = format_node_set(candidate_contact_nodes)
    deck.node_groups.append(
f"""/GRNOD/NODE/10/0
SANDWICH_CONTACT_SLAVE_NODES
{contact_nodes_str}"""
    )

    # GRNOD 20: All honeycomb foil nodes (for foil self-contact)
    all_hex_nodes = sorted(list(hex_nodes.keys()))
    deck.node_groups.append(
f"""/GRNOD/NODE/20/0
ALL_HEX_FOIL_NODES
{format_node_set(all_hex_nodes)}"""
    )

    deck.contacts.append(
f"""/INTER/TYPE7/1
PUNCH_TO_SANDWICH_CONTACT
{10:10d}{1:10d}{4:10d}{0:10d}{3:10d}          {0:10d}{2:10d}{0:10d}{0:10d}
{1.0:20.6f}{0.10:20.6f}{0.0:20.6f}                    {0:10d}{0:10d}
{1000.0:20.6f}{100000.0:20.6f}{0.0:20.6f}{0.0:20.6f}{0:10d}{0:10d}
{1.0:20.6f}{0.25:20.6f}{0.02:20.6f}{0.0:20.6f}{0.0:20.6f}
       000                             1            0.050000            0.000000            0.200000
         0         0            0.000000         2         0         0            0.000000         0"""
    )

    # Contact 2: Top Skin Inner Face to Foil Shells Dedicated Edge-to-Surface (/INTER/TYPE19/2)
    deck.contacts.append(
f"""/INTER/TYPE19/2
TOP_SKIN_TO_FOIL_CONTACT
        20        10         4         0         3         1         0         2         0
            1.000000            0.100000            0.000000
         1000.000000       100000.000000            0.000000            0.000000         0         0
            1.000000            0.200000            0.020000            0.000000            0.000000
       000                             1            0.050000            0.000000            0.200000
         0         0            0.000000         2         0         0"""
    )

    # Contact 3: Bottom Skin Inner Face to Foil Shells Dedicated Edge-to-Surface (/INTER/TYPE19/3)
    deck.contacts.append(
f"""/INTER/TYPE19/3
BOT_SKIN_TO_FOIL_CONTACT
        20        11         4         0         3         1         0         2         0
            1.000000            0.100000            0.000000
         1000.000000       100000.000000            0.000000            0.000000         0         0
            1.000000            0.200000            0.020000            0.000000            0.000000
       000                             1            0.050000            0.000000            0.200000
         0         0            0.000000         2         0         0"""
    )

    # Contact 4: Honeycomb Foil Self-Contact (/INTER/TYPE7/4)
    deck.contacts.append(
f"""/INTER/TYPE7/4
HEX_FOIL_SELF_CONTACT
        20        20         4         0         3         1         0         2         0
            1.000000            0.100000            0.000000
         1000.000000       100000.000000            0.000000            0.000000         0         0
            1.000000            0.200000            0.020000            0.000000            0.000000
       000                             1            0.050000            0.000000            0.200000
         0         0            0.000000         2         0         0"""
    )

    # 11. Boundary Conditions & Kinematics
    # Rigid body for Punch
    punch_nodes_str = format_node_set([n for n in punch_nodes if n != punch_center_id])
    deck.node_groups.append(
f"""/GRNOD/NODE/1/0
PUNCH_NODES_SET
{punch_nodes_str}"""
    )
    deck.bcs.append(
f"""/RBODY/1/0
RIGID_PUNCH
{punch_center_id:10d}         0         0         1     5.000E-04         1         0         1         0
     0.100000            0.100000            0.100000
          0.0                 0.0                 0.0
         0         0         0"""
    )

    # Aperture Support Clamping (r >= 15.0 mm on bottom face z=0)
    support_nodes_str = format_node_set(bot_aperture_clamped_nodes)
    deck.node_groups.append(
f"""/GRNOD/NODE/2/0
SUPPORT_CLAMP_NODES
{support_nodes_str}"""
    )
    deck.bcs.append(
f"""/BCS/1
SUPPORT_APERTURE_CLAMP
   111 111         0         2"""
    )

    # Symmetry X plane (x = 0): Union of solid nodes on x=0 and foil shell nodes on x=0
    all_sym_x_nodes = sorted(list(set(solid_sym_x_nodes + hex_sym_x)))
    sym_x_str = format_node_set(all_sym_x_nodes)
    deck.node_groups.append(
f"""/GRNOD/NODE/21/0
SYMMETRY_X_NODES
{sym_x_str}"""
    )
    deck.bcs.append(
f"""/BCS/2
SYMMETRY_X_PLANE
   100 011         0        21"""
    )

    # Symmetry Y plane (y = 0): Union of solid nodes on y=0 and foil shell nodes on y=0
    all_sym_y_nodes = sorted(list(set(solid_sym_y_nodes + hex_sym_y)))
    sym_y_str = format_node_set(all_sym_y_nodes)
    deck.node_groups.append(
f"""/GRNOD/NODE/22/0
SYMMETRY_Y_NODES
{sym_y_str}"""
    )
    deck.bcs.append(
f"""/BCS/3
SYMMETRY_Y_PLANE
   010 101         0        22"""
    )

    # Punch Master Node Guided Translation in Z only (constrain Ux, Uy, Rot_xyz: code 110 111)
    deck.node_groups.append(
f"""/GRNOD/NODE/3/0
PUNCH_MASTER_NODE_SET
{punch_center_id:10d}"""
    )
    deck.bcs.append(
f"""/BCS/4
PUNCH_MASTER_GUIDE
   110 111         0         3"""
    )

    # Imposed Velocity on Punch Master Node (Smooth Sinusoidal Ramp over 2 ms to v_punch = 1000 mm/s)
    t_ramp = 0.002
    n_pts = 10
    ramp_lines = ["/FUNCT/1", "SMOOTH_RAMP_VELOCITY"]
    for i in range(n_pts + 1):
        t_i = i * (t_ramp / n_pts)
        val = -v_punch * 0.5 * (1.0 - np.cos(np.pi * i / n_pts))
        ramp_lines.append(f"{t_i:20.6f}{val:20.6f}")
    ramp_lines.append(f"{1.0:20.6f}{-v_punch:20.6f}")

    deck.bcs.append("\n".join(ramp_lines) + f"""
/IMPVEL/1
IMPOSED_PUNCH_VELOCITY
         1         Z         0         0         3         0         0
{1.0:20.6f}{1.0:20.6f}{0.0:20.6f}{0.0:20.6f}"""
    )

    # Time History Outputs
    deck.time_histories.append(
f"""/TH/NODE/1
PUNCH_DISP
DZ
{punch_center_id:10d}
/TH/RBODY/2
PUNCH_FORCE
FZ
1
/TH/INTER/3
PUNCH_CONTACT_TH
FN
1
/TH/INTER/4
FOIL_SELF_CONTACT_TH
FN
4"""
    )

    return deck, {
        "n_nodes": len(deck.nodes),
        "n_bricks": total_bricks,
        "n_shells": total_shells,
        "punch_center_id": punch_center_id,
        "t_end": t_end,
        "v_punch": v_punch
    }

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parents[2]
    starter_path = base_dir / 'models' / 'phase2_mesoscale' / 'starter' / 'PUNCTURE_MESO_0000.rad'
    engine_path = base_dir / 'models' / 'phase2_mesoscale' / 'engine' / 'PUNCTURE_MESO_0001.rad'

    print("Generating High-Fidelity Phase 2 Quarter Meso-Scale Model (v2.2)...")
    deck, stats = build_phase2_v2_deck()
    deck.write_starter(starter_path)
    deck.write_engine(engine_path, t_stop=stats['t_end'], anim_dt=0.0002, th_dt=0.00001)

    print(f"Starter deck written: {starter_path} ({starter_path.stat().st_size / 1024:.1f} KB)")
    print(f"Engine deck written:  {engine_path} ({engine_path.stat().st_size / 1024:.1f} KB)")
    print("Model generation completed successfully.")
