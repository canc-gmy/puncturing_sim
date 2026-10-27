"""
Full Discrete Meso-Scale Honeycomb Core Generator for Quarter-Symmetry Domain (v3.0)
Generates explicit 3D hexagonal cell walls (shell elements) for the aluminium honeycomb core
across the ENTIRE quadrant (0 <= x <= 50 mm, 0 <= y <= 50 mm) with vertex node merging
and exact symmetry plane classifications on x = 0 and y = 0.
"""

from pathlib import Path
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Dict

@dataclass
class HexCell:
    cx: float
    cy: float
    vertices: list[tuple[float, float]] # 6 in-plane vertices (x, y)

def generate_full_hex_grid(
    x_max: float = 50.0,
    y_max: float = 50.0,
    cell_size: float = 3.175, # 1/8 inch
) -> list[HexCell]:
    s = cell_size / np.sqrt(3.0)
    dx = cell_size
    dy = 1.5 * s

    # Generate cells covering the bounding box with margin
    margin = 2.0 * cell_size
    nx_min = int(np.floor(-margin / dx))
    nx_max = int(np.ceil((x_max + margin) / dx))
    ny_min = int(np.floor(-margin / dy))
    ny_max = int(np.ceil((y_max + margin) / dy))

    cells = []
    for iy in range(ny_min, ny_max + 1):
        y = iy * dy
        x_offset = 0.5 * dx if (iy % 2 != 0) else 0.0
        for ix in range(nx_min, nx_max + 1):
            x = ix * dx + x_offset
            # Only keep cells that could intersect [0, x_max] x [0, y_max]
            if (-s <= x <= x_max + s) and (-s <= y <= y_max + s):
                angles = np.linspace(np.pi / 6.0, 2.0 * np.pi + np.pi / 6.0, 7)[:-1]
                verts = [(x + s * np.cos(a), y + s * np.sin(a)) for a in angles]
                cells.append(HexCell(cx=x, cy=y, vertices=verts))

    return cells

def clip_segment_to_box(p1, p2, x_min=0.0, x_max=50.0, y_min=0.0, y_max=50.0):
    """Liang-Barsky segment clipping algorithm against 2D bounding box."""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1

    p = [-dx, dx, -dy, dy]
    q = [x1 - x_min, x_max - x1, y1 - y_min, y_max - y1]

    u1 = 0.0
    u2 = 1.0

    for i in range(4):
        if abs(p[i]) < 1e-9:
            if q[i] < 0:
                return None # Parallel and outside
        else:
            t = q[i] / p[i]
            if p[i] < 0:
                if t > u1:
                    u1 = t
            elif p[i] > 0:
                if t < u2:
                    u2 = t

    if u1 > u2:
        return None

    cx1 = x1 + u1 * dx
    cy1 = y1 + u1 * dy
    cx2 = x1 + u2 * dx
    cy2 = y1 + u2 * dy

    # Clamp near-boundary values
    if abs(cx1 - x_min) < 1e-4: cx1 = x_min
    if abs(cx1 - x_max) < 1e-4: cx1 = x_max
    if abs(cy1 - y_min) < 1e-4: cy1 = y_min
    if abs(cy1 - y_max) < 1e-4: cy1 = y_max

    if abs(cx2 - x_min) < 1e-4: cx2 = x_min
    if abs(cx2 - x_max) < 1e-4: cx2 = x_max
    if abs(cy2 - y_min) < 1e-4: cy2 = y_min
    if abs(cy2 - y_max) < 1e-4: cy2 = y_max

    # Discard degenerate zero-length segments
    if np.sqrt((cx2 - cx1)**2 + (cy2 - cy1)**2) < 0.1:
        return None

    return (cx1, cy1), (cx2, cy2)

def discretize_full_quarter_cell_walls(
    cells: list[HexCell],
    x_max: float = 50.0,
    y_max: float = 50.0,
    z_min: float = 2.331,
    z_max: float = 17.331,
    n_z_elem: int = 6,
    n_edge_elem: int = 1,
    node_start_id: int = 1,
    elem_start_id: int = 1,
    part_single_foil: int = 21,
    part_double_foil: int = 22,
):
    """
    Clips and discretizes honeycomb foil walls in quadrant 1 ([0, x_max] x [0, y_max]).
    """
    tol = 1e-4

    def round_pt(p):
        return (round(p[0] / tol) * tol, round(p[1] / tol) * tol)

    # 1. Collect unique edges from cell network
    edges = {}
    for cell in cells:
        v = cell.vertices
        for i in range(6):
            p1 = v[i]
            p2 = v[(i + 1) % 6]
            rp1 = round_pt(p1)
            rp2 = round_pt(p2)
            edge_key = tuple(sorted([rp1, rp2]))

            is_ribbon = abs(p1[0] - p2[0]) < 0.25 * abs(p1[1] - p2[1])
            if edge_key not in edges:
                edges[edge_key] = (p1, p2, is_ribbon, 1)
            else:
                p1_old, p2_old, is_ribbon_old, count = edges[edge_key]
                edges[edge_key] = (p1_old, p2_old, is_ribbon_old, count + 1)

    # 2. Clip each edge to [0, x_max] x [0, y_max]
    q1_walls = []
    for (rp1, rp2), (p1, p2, is_ribbon, count) in edges.items():
        res = clip_segment_to_box(p1, p2, x_min=0.0, x_max=x_max, y_min=0.0, y_max=y_max)
        if res is not None:
            (cx1, cy1), (cx2, cy2) = res
            # Check if wall lies on symmetry x=0
            on_x_plane = (cx1 == 0.0 and cx2 == 0.0)
            eff_part = part_single_foil if on_x_plane else (part_double_foil if (is_ribbon or count > 1) else part_single_foil)
            q1_walls.append(((cx1, cy1), (cx2, cy2), eff_part))

    print(f"Total unique cell walls in full Q1 panel (50x50 mm): {len(q1_walls)}")

    # 3. Discretize walls into quad shells and merge common nodes
    nodes = {} # id -> (x, y, z)
    coord_to_node_id = {} # (round_x, round_y, round_z) -> id
    shells = [] # (elem_id, part_id, [n1, n2, n3, n4])

    node_id = node_start_id
    elem_id = elem_start_id
    z_levels = np.linspace(z_min, z_max, n_z_elem + 1)

    sym_x_nodes = set()
    sym_y_nodes = set()
    bot_nodes = set()
    top_nodes = set()

    for (p1, p2, part_id) in q1_walls:
        wall_node_grid = np.zeros((n_edge_elem + 1, n_z_elem + 1), dtype=int)
        t_edge = np.linspace(0.0, 1.0, n_edge_elem + 1)

        for ie, te in enumerate(t_edge):
            x = (1.0 - te) * p1[0] + te * p2[0]
            y = (1.0 - te) * p1[1] + te * p2[1]
            if abs(x) < 1e-4: x = 0.0
            if abs(y) < 1e-4: y = 0.0
            if abs(x - x_max) < 1e-4: x = x_max
            if abs(y - y_max) < 1e-4: y = y_max

            for iz, z in enumerate(z_levels):
                c_key = (round(x / tol) * tol, round(y / tol) * tol, round(z / tol) * tol)
                if c_key in coord_to_node_id:
                    nid = coord_to_node_id[c_key]
                else:
                    nid = node_id
                    nodes[nid] = (x, y, z)
                    coord_to_node_id[c_key] = nid
                    node_id += 1

                    if abs(x) < 1e-5:
                        sym_x_nodes.add(nid)
                    if abs(y) < 1e-5:
                        sym_y_nodes.add(nid)
                    if abs(z - z_min) < 1e-4:
                        bot_nodes.add(nid)
                    if abs(z - z_max) < 1e-4:
                        top_nodes.add(nid)

                wall_node_grid[ie, iz] = nid

        # Build quad shell elements
        for ie in range(n_edge_elem):
            for iz in range(n_z_elem):
                n1 = int(wall_node_grid[ie, iz])
                n2 = int(wall_node_grid[ie + 1, iz])
                n3 = int(wall_node_grid[ie + 1, iz + 1])
                n4 = int(wall_node_grid[ie, iz + 1])
                shells.append((elem_id, part_id, [n1, n2, n3, n4]))
                elem_id += 1

    return nodes, shells, list(sym_x_nodes), list(sym_y_nodes), list(bot_nodes), list(top_nodes), node_id, elem_id

if __name__ == '__main__':
    cells = generate_full_hex_grid(x_max=50.0, y_max=50.0)
    nodes, shells, sym_x, sym_y, bot_n, top_n, next_nid, next_eid = discretize_full_quarter_cell_walls(cells)
    print(f"Total Q1 full foil nodes: {len(nodes)}, shells: {len(shells)}")
    print(f"Symmetry X foil nodes (x=0): {len(sym_x)}")
    print(f"Symmetry Y foil nodes (y=0): {len(sym_y)}")
    print(f"Bottom foil nodes (z=z_min): {len(bot_n)}")
    print(f"Top foil nodes (z=z_max): {len(top_n)}")
