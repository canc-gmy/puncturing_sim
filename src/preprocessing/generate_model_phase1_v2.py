"""
Phase 1: High-Fidelity Homogenized Core Sandwich Puncture Model Generator (v2.1)
Features:
- True cylindrical polar in-plane mesh aligned with Punch (r=12.5mm) and Aperture (r=15.0mm)
- 5 radial ring subdivisions across the 2.5mm shear clearance (dr = 0.5mm)
- Smooth transfinite transition to 100x100mm square outer boundary
- 7 distinct solid element layers per skin (0.333mm each, [0/45/0/45/0/45/0] layup)
- Orthotropic solid property /PROP/TYPE6 (SOL_ORTH) with ply orientation Phi
- Progressive damage /MAT/LAW25 (Chang-Chang) + /FAIL/CHANG
- Non-linear crushable honeycomb core /MAT/LAW28 + /PROP/TYPE6
- Element deletion upon failure (/DT/BRICK/DEL) for smooth penetration through 16.2mm stroke
- Quasi-static loading: indenter speed 100 mm/s with smooth sinusoidal acceleration ramp
- 81 animation states (0.20 mm displacement per frame)
"""

from pathlib import Path
import numpy as np
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from polar_mesh_2d import generate_inplane_mesh
from radioss_writer import RadiossDeck

def build_phase1_v2_deck(
    punch_dia: float = 25.0,
    aperture_dia: float = 30.0,
    v_punch: float = 100.0,   # mm/s = 0.1 m/s explicit quasi-static
    t_end: float = 0.162,     # 162 ms -> 16.2 mm displacement at 100 mm/s
    nc_inplane: int = 8,
    n_core_layers: int = 10,
) -> tuple[RadiossDeck, dict]:
    """
    Constructs the high-fidelity Phase 1 model.
    Units: mm, s, Mg (tonne), N, MPa, mJ
    """
    deck = RadiossDeck(title="PUNCTURE_HOMOG")

    # 1. Geometry & Thicknesses
    t_ply = 0.333          # mm per ply
    n_plies = 7
    t_skin = n_plies * t_ply # 2.331 mm
    h_core = 15.0          # mm
    total_thickness = 2.0 * t_skin + h_core # 19.662 mm

    # Ply layups: [0, 45, 0, 45, 0, 45, 0]
    ply_angles = [0.0, 45.0, 0.0, 45.0, 0.0, 45.0, 0.0]

    # Z-coordinates of layer interfaces
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
    n_z_planes = len(z_layers)
    n_z_layers = n_z_planes - 1

    print(f"Through-thickness discretization: {n_z_layers} element layers ({n_z_planes} z-planes)")
    print(f"Bottom skin: {n_plies} layers, Core: {n_core_layers} layers, Top skin: {n_plies} layers")
    print(f"Total panel thickness: {z_layers[-1]:.3f} mm")

    # 2. In-Plane 2D Mesh
    nodes_2d, quads_2d, bsets = generate_inplane_mesh(nc=nc_inplane, r0=4.0)
    n_nodes_2d = len(nodes_2d)
    n_quads_2d = len(quads_2d)
    print(f"In-plane 2D mesh: {n_nodes_2d} nodes, {n_quads_2d} quads per layer")

    # 3. 3D Sandwich Mesh Extrusion
    node_id = 1
    node_map_3d = {}
    bot_aperture_clamped_nodes = []
    candidate_contact_nodes = []

    r_nodes_2d = np.sqrt(nodes_2d[:, 0]**2 + nodes_2d[:, 1]**2)

    for iz, z in enumerate(z_layers):
        for in2d in range(n_nodes_2d):
            x, y = nodes_2d[in2d]
            deck.add_node(node_id, x, y, z)
            node_map_3d[(in2d, iz)] = node_id

            # Clamping boundary: bottom plane (iz == 0) and r >= 14.999 mm (outside aperture)
            if iz == 0 and r_nodes_2d[in2d] >= 14.999:
                bot_aperture_clamped_nodes.append(node_id)

            # Contact candidate nodes: all nodes in penetration cylinder r <= 18.0 mm
            if r_nodes_2d[in2d] <= 18.0:
                candidate_contact_nodes.append(node_id)

            node_id += 1

    # 4. Define Parts
    # Bottom skin plies (101..107)
    for p_idx in range(n_plies):
        part_id = 101 + p_idx
        prop_id = 101 + p_idx
        mat_id = 1 # LAW25 CFRP
        deck.parts[part_id] = (f"BOT_CFRP_PLY_{p_idx+1}", prop_id, mat_id)

    # Core part (2)
    deck.parts[2] = ("HONEYCOMB_CORE", 2, 2)

    # Top skin plies (108..114)
    for p_idx in range(n_plies):
        part_id = 108 + p_idx
        prop_id = 108 + p_idx
        mat_id = 1 # LAW25 CFRP
        deck.parts[part_id] = (f"TOP_CFRP_PLY_{p_idx+1}", prop_id, mat_id)

    # Punch part (4)
    deck.parts[4] = ("RIGID_STEEL_PUNCH", 4, 4)

    # 5. Create Solid Elements
    elem_id = 1
    for iz in range(n_z_layers):
        if iz < n_plies:
            part_id = 101 + iz
        elif iz >= n_plies + n_core_layers:
            part_id = 108 + (iz - (n_plies + n_core_layers))
        else:
            part_id = 2

        for q in quads_2d:
            n1_2d, n2_2d, n3_2d, n4_2d = q
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
    print(f"Generated {total_bricks} 3D solid brick elements.")

    # 6. Punch Geometry (Rigid Cylindrical Shell Disc, dia=25mm)
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
            deck.add_shell(elem_id, 4, [p1, p4, p3, p2])
            elem_id += 1

    total_shells = len(deck.shells_by_part[4])
    print(f"Generated rigid punch with {len(punch_nodes)} nodes and {total_shells} shell elements.")

    # 7. Properties & Materials Setup
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

    # Core property (2)
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

    # Punch property (4)
    deck.properties.append(
"""/PROP/TYPE1/4/0
PUNCH_SHELL_PROP
         1         2         2         0         0                      0.000000
            0.000000            0.000000            0.000000            0.000000            0.000000
         1                      1.000000            0.833333                   0         0         0"""
    )

    # Materials
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

    # Mat 2: Crushable Honeycomb Core (/MAT/LAW28)
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

    # 8. Boundary Conditions, Contact & Kinematics
    # Candidate contact slave nodes: nodes with r <= 18.0 mm
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

    deck.surfaces.append(
"""/SURF/PART/1
PUNCH_SURFACE
4"""
    )

    # TYPE7 Penalty Contact
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

    # Rigid Body for Punch
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

    # Imposed Velocity on Punch Master Node (Smooth Sinusoidal Ramp over 10 ms)
    deck.node_groups.append(
f"""/GRNOD/NODE/3/0
PUNCH_MASTER_NODE_SET
{punch_center_id:10d}"""
    )

    t_ramp = 0.010
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
1"""
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
    starter_path = base_dir / 'models' / 'phase1_homogenized' / 'starter' / 'PUNCTURE_HOMOG_0000.rad'
    engine_path = base_dir / 'models' / 'phase1_homogenized' / 'engine' / 'PUNCTURE_HOMOG_0001.rad'

    print("Generating High-Fidelity Phase 1 Polar Composite Model (v2.1)...")
    deck, stats = build_phase1_v2_deck()
    deck.write_starter(starter_path)
    deck.write_engine(engine_path, t_stop=stats['t_end'], anim_dt=0.002, th_dt=0.0001)

    print(f"Starter deck written: {starter_path} ({starter_path.stat().st_size / 1024:.1f} KB)")
    print(f"Engine deck written:  {engine_path} ({engine_path.stat().st_size / 1024:.1f} KB)")
    print("Model generation completed successfully.")
