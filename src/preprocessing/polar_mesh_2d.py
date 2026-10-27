"""
2D Polar-to-Cartesian In-Plane Mesh Generator (v2.0)
Generates a conformal quad mesh with:
1. Central square patch: [-r0, r0] x [-r0, r0] (r0 = 4.0 mm)
2. Smooth blended ring transitioning from square to circular disk at R = 8.0 mm
3. Circular rings:
   - r = 8.0 mm
   - r = 10.5 mm
   - r = 12.5 mm (PUNCH PERIMETER!)
   - r = 13.0, 13.5, 14.0, 14.5, 15.0 mm (5 shear clearance rings, dr = 0.5 mm, APERTURE PERIMETER!)
   - r = 17.5, 21.0, 25.0 mm (shear dissipation zone)
4. Smooth transfinite interpolation transitioning to outer 100x100mm square boundary
"""

import numpy as np
from typing import Tuple, List, Dict

def generate_inplane_mesh(nc: int = 8, r0: float = 4.0) -> Tuple[np.ndarray, List[List[int]], Dict[str, List[int]]]:
    """
    Generates 2D nodes and quad elements.
    Returns:
        nodes: (N_nodes, 2) array of [x, y] coordinates
        quads: list of [n1, n2, n3, n4] 0-based node indices in counter-clockwise order
        boundary_sets: dictionary containing sets of node indices
    """
    n_per_side = nc
    Ntheta = 4 * n_per_side

    # 1. Central Square: [-r0, r0] x [-r0, r0]
    x_c = np.linspace(-r0, r0, n_per_side + 1)
    y_c = np.linspace(-r0, r0, n_per_side + 1)

    nodes_list = []
    node_map_central = {}

    for j in range(n_per_side + 1):
        for i in range(n_per_side + 1):
            nid = len(nodes_list)
            nodes_list.append([x_c[i], y_c[j]])
            node_map_central[(i, j)] = nid

    quads = []
    for j in range(n_per_side):
        for i in range(n_per_side):
            n1 = node_map_central[(i, j)]
            n2 = node_map_central[(i+1, j)]
            n3 = node_map_central[(i+1, j+1)]
            n4 = node_map_central[(i, j+1)]
            quads.append([n1, n2, n3, n4])

    # Extract perimeter nodes of central square in CCW order
    central_perim = []
    for i in range(n_per_side):
        central_perim.append(node_map_central[(i, 0)])
    for j in range(n_per_side):
        central_perim.append(node_map_central[(n_per_side, j)])
    for i in range(n_per_side, 0, -1):
        central_perim.append(node_map_central[(i, n_per_side)])
    for j in range(n_per_side, 0, -1):
        central_perim.append(node_map_central[(0, j)])

    assert len(central_perim) == Ntheta

    perim_pts = np.array([nodes_list[nid] for nid in central_perim])
    thetas = np.arctan2(perim_pts[:, 1], perim_pts[:, 0])
    thetas = np.mod(thetas + 2*np.pi, 2*np.pi)
    
    sort_idx = np.argsort(thetas)
    central_ring = [central_perim[k] for k in sort_idx]
    base_thetas = thetas[sort_idx]

    # 2. Smooth Blended Transition from Square to Circular Disk at R = 8.0 mm
    R_circle_start = 8.0
    u_blend = [0.5, 1.0] # 2 blended rings
    prev_ring = central_ring

    for u in u_blend:
        cur_ring = []
        for it in range(Ntheta):
            th = base_thetas[it]
            cos_t = np.cos(th)
            sin_t = np.sin(th)
            r_sq = r0 / max(abs(cos_t), abs(sin_t))
            r_interp = (1.0 - u) * r_sq + u * R_circle_start
            x = r_interp * cos_t
            y = r_interp * sin_t
            nid = len(nodes_list)
            nodes_list.append([x, y])
            cur_ring.append(nid)

        for it in range(Ntheta):
            it_next = (it + 1) % Ntheta
            n1 = prev_ring[it]
            n2 = cur_ring[it]
            n3 = cur_ring[it_next]
            n4 = prev_ring[it_next]
            quads.append([n1, n2, n3, n4])

        prev_ring = cur_ring

    # 3. Concentric Circular Rings
    # Radii definitions:
    # r = 10.5 mm
    # r = 12.5 mm (PUNCH PERIMETER!)
    # r = 13.0, 13.5, 14.0, 14.5, 15.0 mm (5 shear clearance rings, APERTURE PERIMETER!)
    # r = 17.5, 21.0, 25.0 mm (Outer transition)
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
            x = r * np.cos(th)
            y = r * np.sin(th)
            nid = len(nodes_list)
            nodes_list.append([x, y])
            cur_ring.append(nid)

        for it in range(Ntheta):
            it_next = (it + 1) % Ntheta
            n1 = prev_ring[it]
            n2 = cur_ring[it]
            n3 = cur_ring[it_next]
            n4 = prev_ring[it_next]
            quads.append([n1, n2, n3, n4])

        prev_ring = cur_ring
        if np.isclose(r, 12.5):
            punch_ring = cur_ring
        if np.isclose(r, 15.0):
            aperture_ring = cur_ring

    # 4. Transition from r = 25.0 mm to Outer Square [-50, 50] x [-50, 50]
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

            x = r_interp * cos_t
            y = r_interp * sin_t
            nid = len(nodes_list)
            nodes_list.append([x, y])
            cur_ring.append(nid)

        for it in range(Ntheta):
            it_next = (it + 1) % Ntheta
            n1 = prev_ring[it]
            n2 = cur_ring[it]
            n3 = cur_ring[it_next]
            n4 = prev_ring[it_next]
            quads.append([n1, n2, n3, n4])

        prev_ring = cur_ring

    outer_boundary_ring = prev_ring
    nodes = np.array(nodes_list)

    # Classify nodes for boundary conditions and contact
    r_all = np.sqrt(nodes[:, 0]**2 + nodes[:, 1]**2)
    center_nodes = [i for i, r in enumerate(r_all) if r <= 12.501]
    shear_band_nodes = [i for i, r in enumerate(r_all) if 12.499 <= r <= 15.001]
    support_clamped_nodes = [i for i, r in enumerate(r_all) if r >= 14.999]

    boundary_sets = {
        'punch_nodes': center_nodes,
        'punch_perimeter': punch_ring,
        'shear_band': shear_band_nodes,
        'aperture_perimeter': aperture_ring,
        'support_clamped': support_clamped_nodes,
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
    nodes, quads, bsets = generate_inplane_mesh(nc=8, r0=4.0)
    print(f"Total 2D in-plane nodes: {len(nodes)}")
    print(f"Total 2D in-plane quads: {len(quads)}")
    print(f"Punch perimeter nodes (r=12.5mm): {len(bsets['punch_perimeter'])}")
    print(f"Aperture perimeter nodes (r=15.0mm): {len(bsets['aperture_perimeter'])}")
    print(f"Shear band nodes (12.5 <= r <= 15.0): {len(bsets['shear_band'])}")
    print(f"Support clamp candidate nodes (r >= 15.0): {len(bsets['support_clamped'])}")
