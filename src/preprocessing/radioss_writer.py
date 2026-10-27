"""
OpenCourant / OpenRadioss Input Deck (.rad) Writer
Provides clean, formatted generation of Starter (_0000.rad) and Engine (_0001.rad) files.
"""

from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Node:
    id: int
    x: float
    y: float
    z: float

@dataclass
class Brick8:
    id: int
    n: list[int]  # 8 node IDs

@dataclass
class Shell4:
    id: int
    n: list[int]  # 4 node IDs

class RadiossDeck:
    def __init__(self, title: str = "PUNCTURE_HOMOG"):
        self.title = title
        self.nodes: dict[int, Node] = {}
        self.bricks_by_part: dict[int, list[Brick8]] = defaultdict(list)
        self.shells_by_part: dict[int, list[Shell4]] = defaultdict(list)
        self.parts: dict[int, tuple[str, int, int]] = {}  # part_id -> (name, prop_id, mat_id)
        self.materials: list[str] = []
        self.properties: list[str] = []
        self.node_groups: list[str] = []
        self.surfaces: list[str] = []
        self.contacts: list[str] = []
        self.bcs: list[str] = []
        self.time_histories: list[str] = []

    def add_node(self, node_id: int, x: float, y: float, z: float) -> int:
        self.nodes[node_id] = Node(node_id, float(x), float(y), float(z))
        return node_id

    def add_brick(self, elem_id: int, part_id: int, node_ids: list[int]):
        assert len(node_ids) == 8
        self.bricks_by_part[part_id].append(Brick8(elem_id, node_ids))

    def add_shell(self, elem_id: int, part_id: int, node_ids: list[int]):
        assert len(node_ids) == 4
        self.shells_by_part[part_id].append(Shell4(elem_id, node_ids))

    def write_starter(self, filepath: Path):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write("#RADIOSS STARTER\n")
            f.write("/BEGIN\n")
            f.write(f"{self.title[:80]}\n")
            f.write("2026\n")
            f.write(f"{'Mg':<20}{'mm':<20}{'s':<20}\n")
            f.write(f"{'Mg':<20}{'mm':<20}{'s':<20}\n")
            
            # Nodes
            f.write("/NODE\n")
            for nid in sorted(self.nodes.keys()):
                node = self.nodes[nid]
                f.write(f"{node.id:10d}{node.x:20.6f}{node.y:20.6f}{node.z:20.6f}\n")

            # Parts
            for part_id, (name, prop_id, mat_id) in self.parts.items():
                f.write(f"/PART/{part_id}\n")
                f.write(f"{name}\n")
                f.write(f"{prop_id:10d}{mat_id:10d}         0\n")

            # Properties
            for prop in self.properties:
                f.write(prop + "\n")

            # Materials
            for mat in self.materials:
                f.write(mat + "\n")

            # Solid Elements grouped by part
            for part_id, bricks in self.bricks_by_part.items():
                f.write(f"/BRICK/{part_id}\n")
                for b in bricks:
                    f.write(f"{b.id:10d}" + "".join(f"{n:10d}" for n in b.n) + "\n")

            # Shell Elements grouped by part
            for part_id, shells in self.shells_by_part.items():
                f.write(f"/SHELL/{part_id}\n")
                for s in shells:
                    f.write(f"{s.id:10d}" + "".join(f"{n:10d}" for n in s.n) + "\n")

            # Node Groups
            for grnod in self.node_groups:
                f.write(grnod + "\n")

            # Surfaces
            for surf in self.surfaces:
                f.write(surf + "\n")

            # Contacts / Interfaces
            for contact in self.contacts:
                f.write(contact + "\n")

            # Boundary Conditions
            for bc in self.bcs:
                f.write(bc + "\n")

            # Time Histories
            for th in self.time_histories:
                f.write(th + "\n")

            f.write("/END\n")

    def write_engine(self, filepath: Path, t_stop: float = 0.016, anim_dt: float = 0.0005, th_dt: float = 0.00005):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write("#RADIOSS ENGINE\n")
            f.write("/VERS/2026\n")
            f.write(f"/RUN/{self.title[:20]}/1\n")
            f.write(f"{t_stop:16.6f}\n")
            f.write(f"/ANIM/DT\n")
            f.write(f"0.0 {anim_dt:16.6f}\n")
            f.write("/PRINT/-100\n")
            f.write("/ANIM/VECT/DISP\n")
            f.write("/ANIM/VECT/CONT\n")
            f.write("/ANIM/BRICK/TENS/STRESS/ALL\n")
            f.write("/ANIM/ELEM/ENERGY\n")
            f.write(f"/TFILE\n")
            f.write(f"{th_dt:16.6f}\n")
            f.write("/DT/NODA/CST\n")
            f.write("0.900000        2.500000E-08\n")
            f.write("/DT/BRICK/DEL\n")
            f.write("0.900000        1.000000E-08\n")
            f.write("/DT/SHELL/DEL\n")
            f.write("0.900000        1.000000E-08\n")
            f.write("/END\n")
