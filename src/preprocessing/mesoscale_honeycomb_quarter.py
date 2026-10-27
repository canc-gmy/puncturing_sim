"""
Meso-Scale Honeycomb Core Generator for Quarter-Symmetry Domain (v2.2)
Generates explicit 3D hexagonal cell walls (shell elements) for the aluminium honeycomb core
in the first quadrant (x >= 0, y >= 0, r <= r_patch) with vertex node merging and symmetry classification.
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

def generate_hex_grid(
    r_patch: float = 18.0,
    cell_size: float = 3.175, # 1/8 inch
) -> list[HexCell]:
    s = cell_size / np.sqrt(3.0)
    dx = cell_size
    dy = 1.5 * s

    nx = int(np.ceil((r_patch + cell_size) / dx)) + 1
    ny = int(np.ceil((r_patch + cell_size) / dy)) + 1

    cells = []
    for iy in range(-ny, ny + 1):
        y = iy * dy
        x_offset = 0.5 * dx if (iy % 2 != 0) else 0.0
        for ix in range(-nx, nx + 1):
            x = ix * dx + x_offset
            dist = np.sqrt(x**2 + y**2)
            if dist <= r_patch:
                angles = np.linspace(np.pi / 6.0, 2.0 * np.pi + np.pi / 6.0, 7)[:-1]
                verts = [(x + s * np.cos(a), y + s * np.sin(a)) for a in angles]
                cells.append(HexCell(cx=x, cy=y, vertices=verts))

    return cells

def discretize_quarter_cell_walls(
    cells: list[HexCell],
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
    Extracts, clips, and discretizes honeycomb foil walls in quadrant 1 (x >= 0, y >= 0).
    """
    tol = 1e-4

    def round_pt(p):
        return (round(p[0] / tol) * tol, round(p[1] / tol) * tol)

    # 1. Collect all unique edges across full grid
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

    # 2. Filter and clip edges to Quadrant 1 (x >= 0, y >= 0)
    q1_walls = []
    for (rp1, rp2), (p1, p2, is_ribbon, count) in edges.items():
        x1, y1 = p1
        x2, y2 = p2

        # Case A: Both endpoints in Q1 (with tolerance)
        if x1 >= -1e-5 and x2 >= -1e-5 and y1 >= -1e-5 and y2 >= -1e-5:
            cx1 = 0.0 if abs(x1) < 1e-4 else float(x1)
            cy1 = 0.0 if abs(y1) < 1e-4 else float(y1)
            cx2 = 0.0 if abs(x2) < 1e-4 else float(x2)
            cy2 = 0.0 if abs(y2) < 1e-4 else float(y2)

            # If edge lies directly on x=0 plane, it is split in half across its thickness
            on_x_plane = (cx1 == 0.0 and cx2 == 0.0)
            eff_part = part_single_foil if on_x_plane else (part_double_foil if (is_ribbon or count > 1) else part_single_foil)
            q1_walls.append(((cx1, cy1), (cx2, cy2), eff_part))

        # Case B: Vertical ribbon crossing y=0 with x >= 0
        elif (x1 >= -1e-5 or x2 >= -1e-5) and ((y1 < -1e-5 and y2 > 1e-5) or (y1 > 1e-5 and y2 < -1e-5)):
            x_val = 0.0 if abs((x1 + x2) / 2.0) < 1e-4 else float((x1 + x2) / 2.0)
            y_top = float(max(y1, y2))
            eff_part = part_double_foil if (is_ribbon or count > 1) else part_single_foil
            q1_walls.append(((x_val, 0.0), (x_val, y_top), eff_part))

    print(f"Total unique cell walls in Q1 patch: {len(q1_walls)}")

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
            if abs(x) < 1e-4:
                x = 0.0
            if abs(y) < 1e-4:
                y = 0.0

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
    cells = generate_hex_grid(r_patch=18.0)
    nodes, shells, sym_x, sym_y, bot_n, top_n, next_nid, next_eid = discretize_quarter_cell_walls(cells)
    print(f"Total Q1 foil nodes: {len(nodes)}, shells: {len(shells)}")
    print(f"Symmetry X foil nodes (x=0): {len(sym_x)}")
    print(f"Symmetry Y foil nodes (y=0): {len(sym_y)}")
    print(f"Bottom foil nodes (z=z_min): {len(bot_n)}")
    print(f"Top foil nodes (z=z_max): {len(top_n)}")
