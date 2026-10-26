"""
Meso-Scale Honeycomb Core Generator (with Vertex Node Merging)
Generates explicit 3D hexagonal cell walls (shell elements) for the aluminium honeycomb core
in the central puncture zone according to the IMATEC Alloy 5052 - 1/8" - 6.1 pcf datasheet.
"""

from pathlib import Path
import numpy as np
from dataclasses import dataclass

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

def discretize_cell_walls(
    cells: list[HexCell],
    z_min: float = 2.331,
    z_max: float = 17.331,
    n_z_elem: int = 5,
    n_edge_elem: int = 2,
    node_start_id: int = 1,
    elem_start_id: int = 1,
    part_single_foil: int = 21,
    part_double_foil: int = 22,
):
    tol = 1e-4

    def round_pt(p):
        return (round(p[0] / tol) * tol, round(p[1] / tol) * tol)

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

    print(f"Total unique cell walls in patch: {len(edges)}")

    nodes = {} # id -> (x, y, z)
    coord_to_node_id = {} # (round_x, round_y, round_z) -> id
    shells = [] # (elem_id, part_id, [n1, n2, n3, n4])

    node_id = node_start_id
    elem_id = elem_start_id
    z_levels = np.linspace(z_min, z_max, n_z_elem + 1)

    for (rp1, rp2), (p1, p2, is_ribbon, count) in edges.items():
        part_id = part_double_foil if (is_ribbon or count > 1) else part_single_foil
        
        wall_node_grid = np.zeros((n_edge_elem + 1, n_z_elem + 1), dtype=int)
        t_edge = np.linspace(0.0, 1.0, n_edge_elem + 1)

        for ie, te in enumerate(t_edge):
            x = (1.0 - te) * p1[0] + te * p2[0]
            y = (1.0 - te) * p1[1] + te * p2[1]
            for iz, z in enumerate(z_levels):
                c_key = (round(x / tol) * tol, round(y / tol) * tol, round(z / tol) * tol)
                if c_key in coord_to_node_id:
                    nid = coord_to_node_id[c_key]
                else:
                    nid = node_id
                    nodes[nid] = (x, y, z)
                    coord_to_node_id[c_key] = nid
                    node_id += 1

                wall_node_grid[ie, iz] = nid

        # Create 4-node shells
        for ie in range(n_edge_elem):
            for iz in range(n_z_elem):
                n1 = wall_node_grid[ie, iz]
                n2 = wall_node_grid[ie + 1, iz]
                n3 = wall_node_grid[ie + 1, iz + 1]
                n4 = wall_node_grid[ie, iz + 1]
                shells.append((elem_id, part_id, [n1, n2, n3, n4]))
                elem_id += 1

    print(f"Meso-scale merged unique nodes: {len(nodes)}")
    print(f"Meso-scale shells created: {len(shells)}")
    return nodes, shells, node_id, elem_id

if __name__ == '__main__':
    cells = generate_hex_grid(r_patch=18.0)
    print(f"Generated {len(cells)} hexagonal cells in puncture zone.")
    nodes, shells, _, _ = discretize_cell_walls(cells)
