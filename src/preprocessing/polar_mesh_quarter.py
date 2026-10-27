"""
2D Polar-to-Cartesian Quarter Mesh Generator (v2.2)
Generates a conformal quad mesh for quadrant 1 (x >= 0, y >= 0):
1. Central quadrant square patch: [0, r0] x [0, r0] (r0 = 4.0 mm)
2. Smooth blended ring transitioning from square quadrant to circular sector at R = 8.0 mm
3. Circular rings (theta in [0, pi/2]):
   - r = 8.0 mm
   - r = 10.5 mm
   - r = 12.5 mm (PUNCH PERIMETER!)
   - r = 13.0, 13.5, 14.0, 14.5, 15.0 mm (5 shear clearance rings, dr = 0.5 mm, APERTURE PERIMETER!)
   - r = 17.5, 21.0, 25.0 mm (shear dissipation zone)
4. Smooth transfinite interpolation transitioning to outer 50x50 mm square boundary
"""

import numpy as np
from typing import Tuple, List, Dict

def generate_quarter_inplane_mesh(nc: int = 8, r0: float = 4.0) -> Tuple[np.ndarray, List[List[int]], Dict[str, List[int]]]:
    """
    Generates 2D nodes and quad elements for quadrant 1: [0, 50] x [0, 50] mm.
    Returns:
        nodes: (N_nodes, 2) array of [x, y] coordinates
        quads: list of [n1, n2, n3, n4] 0-based node indices in counter-clockwise order
        boundary_sets: dictionary containing sets of node indices
    """
    x_c = np.linspace(0.0, r0, nc + 1)
    y_c = np.linspace(0.0, r0, nc + 1)

    nodes_list = []
    node_map_central = {}

    for j in range(nc + 1):
        for i in range(nc + 1):
            nid = len(nodes_list)
            # Ensure exact zero along symmetry lines
            px = 0.0 if i == 0 else float(x_c[i])
            py = 0.0 if j == 0 else float(y_c[j])
            nodes_list.append([px, py])
            node_map_central[(i, j)] = nid

    quads = []
    for j in range(nc):
        for i in range(nc):
            n1 = node_map_central[(i, j)]
            n2 = node_map_central[(i + 1, j)]
            n3 = node_map_central[(i + 1, j + 1)]
            n4 = node_map_central[(i, j + 1)]
            quads.append([n1, n2, n3, n4])

    # Extract perimeter facing outward into quadrant 1:
    # From (r0, 0) up along x=r0 to (r0, r0), then left along y=r0 to (0, r0).
    central_perim = []
    for j in range(nc + 1):
        central_perim.append(node_map_central[(nc, j)])
    for i in range(nc - 1, -1, -1):
        central_perim.append(node_map_central[(i, nc)])

    Ntheta = len(central_perim) # 2 * nc + 1 nodes (e.g. 17 nodes)
    base_pts = np.array([nodes_list[nid] for nid in central_perim])
    base_thetas = np.arctan2(base_pts[:, 1], base_pts[:, 0])

    # 2. Smooth Blended Transition from Square Quadrant to Circular Sector at R = 8.0 mm
    R_circle_start = 8.0
    u_blend = [0.5, 1.0] # 2 blended rings
    prev_ring = central_perim

    for u in u_blend:
        cur_ring = []
        for it in range(Ntheta):
            th = base_thetas[it]
            cos_t = np.cos(th)
            sin_t = np.sin(th)
            r_sq = r0 / max(abs(cos_t), abs(sin_t))
            r_interp = (1.0 - u) * r_sq + u * R_circle_start

            if it == 0:
                px = float(r_interp)
                py = 0.0
            elif it == Ntheta - 1:
                px = 0.0
                py = float(r_interp)
            else:
                px = float(r_interp * cos_t)
                py = float(r_interp * sin_t)

            nid = len(nodes_list)
            nodes_list.append([px, py])
            cur_ring.append(nid)

        for it in range(Ntheta - 1):
            n1 = prev_ring[it]
            n2 = cur_ring[it]
            n3 = cur_ring[it + 1]
            n4 = prev_ring[it + 1]
            quads.append([n1, n2, n3, n4])

        prev_ring = cur_ring

    # 3. Concentric Circular Rings
    radii_circular = [
        10.5,
        12.5,        # Punch perimeter
        13.0, 13.5, 14.0, 14.5, 15.0,  # 5 shear clearance rings
        17.5, 21.0, 25.0
    ]

    punch_ring = None
    aperture_ring = None

    for r in radii_circular:
        cur_ring = []
        for it in range(Ntheta):
            th = base_thetas[it]
            if it == 0:
                px = float(r)
                py = 0.0
            elif it == Ntheta - 1:
                px = 0.0
                py = float(r)
            else:
                px = float(r * np.cos(th))
                py = float(r * np.sin(th))

            nid = len(nodes_list)
            nodes_list.append([px, py])
            cur_ring.append(nid)

        for it in range(Ntheta - 1):
            n1 = prev_ring[it]
            n2 = cur_ring[it]
            n3 = cur_ring[it + 1]
            n4 = prev_ring[it + 1]
            quads.append([n1, n2, n3, n4])

        prev_ring = cur_ring
        if np.isclose(r, 12.5):
            punch_ring = cur_ring
        if np.isclose(r, 15.0):
            aperture_ring = cur_ring

    # 4. Transition from r = 25.0 mm to Outer Quarter Square [0, 50] x [0, 50] mm
    r_inner = 25.0
    u_steps = [0.25, 0.50, 0.75, 1.00]  # 4 outer rings

    for u in u_steps:
        cur_ring = []
        for it in range(Ntheta):
            th = base_thetas[it]
            cos_t = np.cos(th)
            sin_t = np.sin(th)
            max_c = max(abs(cos_t), abs(sin_t))
            r_sq = 50.0 / max_c
            r_interp = (1.0 - u) * r_inner + u * r_sq

            if it == 0:
                px = float(r_interp)
                py = 0.0
            elif it == Ntheta - 1:
                px = 0.0
                py = float(r_interp)
            else:
                px = float(r_interp * cos_t)
                py = float(r_interp * sin_t)

            nid = len(nodes_list)
            nodes_list.append([px, py])
            cur_ring.append(nid)

        for it in range(Ntheta - 1):
            n1 = prev_ring[it]
            n2 = cur_ring[it]
            n3 = cur_ring[it + 1]
            n4 = prev_ring[it + 1]
            quads.append([n1, n2, n3, n4])

        prev_ring = cur_ring

    outer_boundary_ring = prev_ring
    nodes = np.array(nodes_list)

    # Classify nodes for boundary conditions and contact
    r_all = np.sqrt(nodes[:, 0]**2 + nodes[:, 1]**2)
    center_nodes = [i for i, r in enumerate(r_all) if r <= 12.501]
    shear_band_nodes = [i for i, r in enumerate(r_all) if 12.499 <= r <= 15.001]
    support_clamped_nodes = [i for i, r in enumerate(r_all) if r >= 14.999]
    sym_x_nodes = [i for i, (x, y) in enumerate(nodes) if abs(x) < 1e-5]
    sym_y_nodes = [i for i, (x, y) in enumerate(nodes) if abs(y) < 1e-5]

    boundary_sets = {
        'punch_nodes': center_nodes,
        'punch_perimeter': punch_ring,
        'shear_band': shear_band_nodes,
        'aperture_perimeter': aperture_ring,
        'support_clamped': support_clamped_nodes,
        'sym_x': sym_x_nodes,
        'sym_y': sym_y_nodes,
        'outer_boundary': outer_boundary_ring
    }

    # Verify quad element quality (Jacobian / area > 0)
    for q_idx, (n1, n2, n3, n4) in enumerate(quads):
        p1, p2, p3, p4 = nodes[n1], nodes[n2], nodes[n3], nodes[n4]
        v21 = p2 - p1
        v31 = p3 - p1
        v41 = p4 - p1
        area1 = 0.5 * (v21[0] * v31[1] - v21[1] * v31[0])
        area2 = 0.5 * (v31[0] * v41[1] - v31[1] * v41[0])
        if area1 <= 1e-6 or area2 <= 1e-6:
            raise ValueError(f"Degenerate or inverted quad element {q_idx}: areas {area1:.4e}, {area2:.4e}")

    return nodes, quads, boundary_sets

if __name__ == '__main__':
    nodes, quads, bsets = generate_quarter_inplane_mesh(nc=8, r0=4.0)
    print(f"Total 2D quarter in-plane nodes: {len(nodes)}")
    print(f"Total 2D quarter in-plane quads: {len(quads)}")
    print(f"Punch perimeter nodes (r=12.5mm): {len(bsets['punch_perimeter'])}")
    print(f"Aperture perimeter nodes (r=15.0mm): {len(bsets['aperture_perimeter'])}")
    print(f"Shear band nodes (12.5 <= r <= 15.0): {len(bsets['shear_band'])}")
    print(f"Support clamp candidate nodes (r >= 15.0): {len(bsets['support_clamped'])}")
    print(f"Symmetry X nodes (x=0): {len(bsets['sym_x'])}")
    print(f"Symmetry Y nodes (y=0): {len(bsets['sym_y'])}")
