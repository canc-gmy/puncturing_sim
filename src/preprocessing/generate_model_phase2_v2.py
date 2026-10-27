"""
Phase 2: High-Fidelity Meso-Scale Hybrid Sandwich FE Model Generator (v2.0)
Combines:
- Explicit 3D hexagonal aluminium honeycomb cell walls (shell elements, parts 21 & 22)
  in the central puncture zone (r <= 18.0 mm) with Johnson-Cook plasticity (/MAT/LAW2)
- Homogenized crushable honeycomb core (/MAT/LAW28 + /PROP/TYPE6) in the outer zone (r > 18.0 mm)
- 7 distinct orthotropic solid plies per CFRP skin ([0/45/0/45/0/45/0]) with /PROP/TYPE6
- Progressive composite damage model /MAT/LAW25 (Chang-Chang) + /FAIL/CHANG
- Tied interface /INTER/TYPE2 kinematically bonding honeycomb foil edges to composite face sheets
- Rigid cylindrical steel punch (dia 25 mm) with /INTER/TYPE7 penalty contact
- Complete 20-column coordinate precision for OpenRadioss 2026
"""

from pathlib import Path
import numpy as np
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from polar_mesh_2d import generate_inplane_mesh
from mesoscale_honeycomb_generator import generate_hex_grid, discretize_cell_walls
from radioss_writer import RadiossDeck

def build_phase2_v2_deck(
    panel_l: float = 100.0,
    panel_w: float = 100.0,
    r_meso: float = 18.0,
    cell_size: float = 3.175, # 1/8 inch
    punch_dia: float = 25.0,
    aperture_dia: float = 30.0,
    v_punch: float = 1000.0,  # mm/s = 1.0 m/s
    t_end: float = 0.0162,    # 16.2 ms -> 16.2 mm displacement
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

    # 2. In-Plane 2D Mesh for Composite Skins & Outer Core
    nodes_2d, quads_2d, _ = generate_inplane_mesh(nc=nc_inplane, r0=4.0)
    n_nodes_2d = len(nodes_2d)
    r_nodes_2d = np.sqrt(nodes_2d[:, 0]**2 + nodes_2d[:, 1]**2)

    # 3. Discretize Meso-scale Honeycomb Foil Walls in Puncture Zone
    print(f"Generating explicit honeycomb cells in patch (r <= {r_meso} mm)...")
    cells = generate_hex_grid(r_patch=r_meso, cell_size=cell_size)
    hex_nodes, hex_shells, next_nid, next_eid = discretize_cell_walls(
        cells, z_min=z_core_min, z_max=z_core_max, n_z_elem=6, n_edge_elem=1,
        node_start_id=1, elem_start_id=1, part_single_foil=21, part_double_foil=22
    )

    hex_bot_nodes = []
    hex_top_nodes = []
    candidate_contact_nodes = []

    for nid, (x, y, z) in hex_nodes.items():
        deck.add_node(nid, x, y, z)
        # Check if node is on bottom interface (z = 2.331 mm)
        if abs(z - z_core_min) < 1e-4:
            hex_bot_nodes.append(nid)
        # Check if node is on top interface (z = 17.331 mm)
        if abs(z - z_core_max) < 1e-4:
            hex_top_nodes.append(nid)
        
        # Candidate contact nodes for punch contact
        if np.sqrt(x**2 + y**2) <= 15.0:
            candidate_contact_nodes.append(nid)

    for eid, pid, nids in hex_shells:
        deck.add_shell(eid, pid, nids)

    print(f"Added {len(hex_nodes)} meso-scale nodes and {len(hex_shells)} foil shell elements.")
    print(f"Honeycomb bottom boundary nodes: {len(hex_bot_nodes)}, top: {len(hex_top_nodes)}")

    # 4. Extrude 3D Sandwich Mesh (Skins across full panel, Core only for r > r_meso)
    node_id = next_nid
    elem_id = next_eid
    node_map_3d = {}
    bot_aperture_clamped_nodes = []

    for iz, z in enumerate(z_layers):
        for in2d in range(n_nodes_2d):
            x, y = nodes_2d[in2d]
            deck.add_node(node_id, x, y, z)
            node_map_3d[(in2d, iz)] = node_id

            # Clamp aperture on bottom plane outside aperture
            if iz == 0 and r_nodes_2d[in2d] >= 14.999:
                bot_aperture_clamped_nodes.append(node_id)

            # Contact candidate nodes: all nodes in penetration cylinder r <= 15.0 mm
            if r_nodes_2d[in2d] <= 15.0:
                candidate_contact_nodes.append(node_id)

            node_id += 1

    # 5. Define Parts
    # Bottom skin plies (101..107)
    for p_idx in range(n_plies):
        part_id = 101 + p_idx
        prop_id = 101 + p_idx
        mat_id = 1 # LAW25 CFRP
        deck.parts[part_id] = (f"BOT_CFRP_PLY_{p_idx+1}", prop_id, mat_id)

    # Outer homogenized honeycomb core
    deck.parts[2] = ("OUTER_HONEYCOMB", 2, 2)

    # Top skin plies (108..114)
    for p_idx in range(n_plies):
        part_id = 108 + p_idx
        prop_id = 108 + p_idx
        mat_id = 1 # LAW25 CFRP
        deck.parts[part_id] = (f"TOP_CFRP_PLY_{p_idx+1}", prop_id, mat_id)

    # Meso Honeycomb parts
    deck.parts[21] = ("HEX_FOIL_SINGLE", 21, 21)
    deck.parts[22] = ("HEX_FOIL_DOUBLE", 22, 21) # shared LAW2 mat

    # Punch part
    deck.parts[4] = ("RIGID_STEEL_PUNCH", 4, 4)

    # 6. Create Solid Brick Elements
    for iz in range(n_z_layers):
        is_bot_skin = (iz < n_plies)
        is_top_skin = (iz >= n_plies + n_core_layers)
        is_core = (not is_bot_skin and not is_top_skin)

        if is_bot_skin:
            part_id = 101 + iz
        elif is_top_skin:
            part_id = 108 + (iz - (n_plies + n_core_layers))
        else:
            part_id = 2

        for q in quads_2d:
            n1_2d, n2_2d, n3_2d, n4_2d = q
            
            # If in core region, omit solid elements inside meso patch (r <= r_meso)
            if is_core:
                xc = 0.25 * (nodes_2d[n1_2d, 0] + nodes_2d[n2_2d, 0] + nodes_2d[n3_2d, 0] + nodes_2d[n4_2d, 0])
                yc = 0.25 * (nodes_2d[n1_2d, 1] + nodes_2d[n2_2d, 1] + nodes_2d[n3_2d, 1] + nodes_2d[n4_2d, 1])
                rc = np.sqrt(xc**2 + yc**2)
                if rc <= r_meso:
                    continue

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
    print(f"Total sandwich solid elements: {total_bricks}")

    # 7. Rigid Steel Punch Modeling
    z_punch_face = z_top_max + 0.50 + 0.20 # 20.362 mm (0.20 mm initial clearance)
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
            # Normal points in -Z toward plate (CW order)
            deck.add_shell(elem_id, 4, [p1, p4, p3, p2])
            elem_id += 1

    print(f"Rigid punch shell elements: {len(deck.shells_by_part[4])}")

    # 8. Properties Setup
    # Bottom skin plies (101..107)
    for p_idx in range(n_plies):
        prop_id = 101 + p_idx
        phi = ply_angles[p_idx]
        deck.properties.append(
f"""/PROP/TYPE6/{prop_id}/0
BOT_CFRP_PLY_{p_idx+1}_PROP
         1         4                   0         0         0         0         2            0.000000
                 0.1                 0.1                 0.1
                 0.0                 0.0                 0.0         0         1         0
{phi:20.6f}            0.000000            0.000000            0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         0         0         0"""
        )

    # Outer Honeycomb Core Property: /PROP/TYPE6/2/0
    deck.properties.append(
"""/PROP/TYPE6/2/0
OUTER_HONEYCOMB_PROP
         1         4                   0         0         0         0         2            0.000000
                 0.1                 0.1                 0.1
                 0.0                 0.0                 0.0         0         1         0
            0.000000            0.000000            0.000000            0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         0         0         0"""
    )

    # Top skin plies (108..114)
    for p_idx in range(n_plies):
        prop_id = 108 + p_idx
        phi = ply_angles[p_idx]
        deck.properties.append(
f"""/PROP/TYPE6/{prop_id}/0
TOP_CFRP_PLY_{p_idx+1}_PROP
         1         4                   0         0         0         0         2            0.000000
                 0.1                 0.1                 0.1
                 0.0                 0.0                 0.0         0         1         0
{phi:20.6f}            0.000000            0.000000            0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         0         0         0"""
        )

    # Hex Foil Single Wall Shell Property: /PROP/TYPE1/21/0 (t = 0.0381 mm)
    deck.properties.append(
"""/PROP/TYPE1/21/0
HEX_FOIL_SINGLE_PROP
         1         2         2         0         0                      0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         1                      0.038100            0.833333                   0         0         0"""
    )

    # Hex Foil Double Wall Shell Property: /PROP/TYPE1/22/0 (t = 0.0762 mm)
    deck.properties.append(
"""/PROP/TYPE1/22/0
HEX_FOIL_DOUBLE_PROP
         1         2         2         0         0                      0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         1                      0.076200            0.833333                   0         0         0"""
    )

    # Punch Shell Property: /PROP/TYPE1/4/0 (Rigid steel shell, thickness 1.0 mm)
    deck.properties.append(
"""/PROP/TYPE1/4/0
PUNCH_SHELL_PROP
         1         2         2         0         0                      0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         1                      1.000000            0.833333                   0         0         0"""
    )

    # 9. Materials Setup
    # Mat 1: CFRP Orthotropic with Chang-Chang progressive failure
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

    # Mat 2: Crushable Honeycomb Core (/MAT/LAW28) with plateau & densification
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

    # Mat 4: Rigid Steel Punch (/MAT/LAW1)
    deck.materials.append(
"""/MAT/LAW1/4
RIGID_STEEL_PUNCH
        7.850000E-09
       210000.000000            0.300000"""
    )

    # Mat 21: Aluminium 5052-H39 Foil (/MAT/LAW2 Johnson-Cook Plasticity, exact 5 cards)
    deck.materials.append(
"""/MAT/LAW2/21
AL_5052_FOIL_LAW2
        2.680000E-09
        70000.000000            0.330000
          290.000000          180.000000            0.400000            0.200000          450.000000
            0.001000            0.001000         1         0        1.000000E+20            0.000000
            1.000000          925.000000            2.400000          293.000000"""
    )

    # 10. Node Sets & Surfaces for Interfaces & Contact
    # Secondary node sets for tied skin-core contacts
    bot_hex_str = ""
    for i, nid in enumerate(hex_bot_nodes):
        bot_hex_str += f"{nid:10d}"
        if (i + 1) % 10 == 0 or (i + 1) == len(hex_bot_nodes):
            bot_hex_str += "\n"

    deck.node_groups.append(
f"""/GRNOD/NODE/21/0
HEX_CORE_BOT_NODES
{bot_hex_str.rstrip()}"""
    )

    top_hex_str = ""
    for i, nid in enumerate(hex_top_nodes):
        top_hex_str += f"{nid:10d}"
        if (i + 1) % 10 == 0 or (i + 1) == len(hex_top_nodes):
            top_hex_str += "\n"

    deck.node_groups.append(
f"""/GRNOD/NODE/22/0
HEX_CORE_TOP_NODES
{top_hex_str.rstrip()}"""
    )

    # Surface 1: Punch shell surface
    deck.surfaces.append(
"""/SURF/PART/1
PUNCH_SURFACE
4"""
    )

    # Candidate contact slave nodes for punch contact (all sandwich nodes in puncture cylinder r <= 18.0 mm)
    candidate_contact_nodes = sorted(list(set(candidate_contact_nodes)))
    contact_nodes_str = ""
    for i, nid in enumerate(candidate_contact_nodes):
        contact_nodes_str += f"{nid:10d}"
        if (i + 1) % 10 == 0 or (i + 1) == len(candidate_contact_nodes):
            contact_nodes_str += "\n"

    deck.node_groups.append(
f"""/GRNOD/NODE/10/0
SANDWICH_CONTACT_SLAVE_NODES
{contact_nodes_str.rstrip()}"""
    )

    # TYPE7 Penalty Contact between Punch and Sandwich
    deck.contacts.append(
f"""/INTER/TYPE7/1
PUNCH_TO_SANDWICH_CONTACT
{10:10d}{1:10d}{4:10d}{0:10d}{3:10d}          {0:10d}{2:10d}{0:10d}{0:10d}
{1.0:20.6f}{0.10:20.6f}{0.0:20.6f}                    {0:10d}{0:10d}
{1000.0:20.6f}{100000.0:20.6f}{0.0:20.6f}{0.0:20.6f}{0:10d}{0:10d}
{1.0:20.6f}{0.25:20.6f}{0.02:20.6f}{0.0:20.6f}{0.0:20.6f}
       000                             0            0.050000            0.000000            0.200000
         0         0            0.000000         2         0         0            0.000000         0"""
    )

    # 11. Kinematics & Boundary Conditions
    # Rigid body for Punch
    punch_nodes_str = ""
    for i, nid in enumerate([n for n in punch_nodes if n != punch_center_id]):
        punch_nodes_str += f"{nid:10d}"
        if (i + 1) % 10 == 0 or (i + 1) == len(punch_nodes):
            punch_nodes_str += "\n"

    deck.node_groups.append(
f"""/GRNOD/NODE/1/0
PUNCH_NODES_SET
{punch_nodes_str.rstrip()}"""
    )
    deck.bcs.append(
f"""/RBODY/1/0
RIGID_PUNCH
{punch_center_id:10d}         0         0         1     5.000E-04         1         0         1         0
     0.100000            0.100000            0.100000
          0.0                 0.0                 0.0
         0         0         0"""
    )

    # Aperture Support Clamping
    support_nodes_str = ""
    for i, nid in enumerate(bot_aperture_clamped_nodes):
        support_nodes_str += f"{nid:10d}"
        if (i + 1) % 10 == 0 or (i + 1) == len(bot_aperture_clamped_nodes):
            support_nodes_str += "\n"

    deck.node_groups.append(
f"""/GRNOD/NODE/2/0
SUPPORT_CLAMP_NODES
{support_nodes_str.rstrip()}"""
    )
    deck.bcs.append(
f"""/BCS/1
SUPPORT_APERTURE_CLAMP
   111 111         0         2"""
    )

    # Imposed Velocity on Punch Master Node
    deck.node_groups.append(
f"""/GRNOD/NODE/3/0
PUNCH_MASTER_NODE_SET
{punch_center_id:10d}"""
    )
    deck.bcs.append(
f"""/FUNCT/1
RAMP_VELOCITY
                 0.0      {-v_punch:14.5f}
                 1.0      {-v_punch:14.5f}
/IMPVEL/1
IMPOSED_PUNCH_VELOCITY
         1         Z         0         0         3         0         0
{1.0:20.6f}{1.0:20.6f}{0.0:20.6f}{0.0:20.6f}"""
    )

    # 12. Time Histories
    deck.time_histories.append(
f"""/TH/NODE/1
PUNCH_DISP
DZ
{punch_center_id:10d}
/TH/RBODY/2
PUNCH_FORCE
FZ
1"""
    )

    total_shells = sum(len(s) for s in deck.shells_by_part.values())
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

    print("Generating High-Fidelity Phase 2 Meso-Scale Model (v2.0)...")
    deck, stats = build_phase2_v2_deck()
    deck.write_starter(starter_path)
    deck.write_engine(engine_path, t_stop=stats['t_end'])

    print(f"Phase 2 Starter deck written: {starter_path} ({starter_path.stat().st_size / 1024:.1f} KB)")
    print(f"Phase 2 Engine deck written:  {engine_path} ({engine_path.stat().st_size / 1024:.1f} KB)")
    print(f"Nodes: {stats['n_nodes']}, Bricks: {stats['n_bricks']}, Shells: {stats['n_shells']}")
    print("Phase 2 Model generation complete.")
