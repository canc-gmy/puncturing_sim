"""
OpenCourant / OpenRadioss Input Deck (.rad) Writer
Provides clean, formatted generation of Starter (_0000.rad) and Engine (_0001.rad) files.
"""

from pathlib import Path
from dataclasses import dataclass, field
import numpy as np

@dataclass
class Node:
    id: int
    x: float
    y: float
    z: float

@dataclass
class Brick8:
    id: int
    part_id: int
    n: list[int]  # 8 node IDs

@dataclass
class Shell4:
    id: int
    part_id: int
    n: list[int]  # 4 node IDs

class RadiossDeck:
    def __init__(self, title: str = "Composite Sandwich Puncture Simulation"):
        self.title = title
        self.nodes: dict[int, Node] = {}
        self.bricks: list[Brick8] = []
        self.shells: list[Shell4] = []
        self.parts: dict[int, str] = {}
        self.materials: list[str] = []
        self.properties: list[str] = []
        self.contacts: list[str] = []
        self.bcs: list[str] = []

    def add_node(self, node_id: int, x: float, y: float, z: float) -> int:
        self.nodes[node_id] = Node(node_id, float(x), float(y), float(z))
        return node_id

    def add_brick(self, elem_id: int, part_id: int, node_ids: list[int]):
        assert len(node_ids) == 8
        self.bricks.append(Brick8(elem_id, part_id, node_ids))

    def add_shell(self, elem_id: int, part_id: int, node_ids: list[int]):
        assert len(node_ids) == 4
        self.shells.append(Shell4(elem_id, part_id, node_ids))

    def write_starter(self, filepath: Path):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(f"# OpenCourant Starter Input Deck\n")
            f.write(f"# Model: {self.title}\n")
            f.write("/BEGIN\n")
            f.write(f"{self.title[:80]}\n")
            f.write("/UNIT/1\n")
            f.write("UNITS DEFINITION\n")
            f.write("#   Unit_mass   Unit_length     Unit_time\n")
            f.write("        Mg              mm               s\n")
            
            # Nodes
            f.write("/NODE\n")
            for nid in sorted(self.nodes.keys()):
                node = self.nodes[nid]
                # Radioss 10-char or 16-char fixed/free format
                f.write(f"{node.id:10d}{node.x:16.6f}{node.y:16.6f}{node.z:16.6f}\n")

            # Solid Elements
            if self.bricks:
                f.write("/BRICK\n")
                for b in self.bricks:
                    f.write(f"{b.id:10d}{b.part_id:10d}" + "".join(f"{n:10d}" for n in b.n) + "\n")

            # Shell Elements
            if self.shells:
                f.write("/SHELL\n")
                for s in self.shells:
                    f.write(f"{s.id:10d}{s.part_id:10d}" + "".join(f"{n:10d}" for n in s.n) + "\n")

            # Custom Parts, Properties, Materials, Contacts, Boundary Conditions
            for prop in self.properties:
                f.write(prop + "\n")

            for mat in self.materials:
                f.write(mat + "\n")

            for part_id, name in self.parts.items():
                f.write(f"/PART/{part_id}\n")
                f.write(f"{name}\n")
                f.write(f"{part_id:10d}{part_id:10d}\n")  # part_id, prop_id, mat_id

            for contact in self.contacts:
                f.write(contact + "\n")

            for bc in self.bcs:
                f.write(bc + "\n")

            f.write("/END\n")

    def write_engine(self, filepath: Path, t_stop: float = 0.025, anim_dt: float = 0.0005, th_dt: float = 0.00005):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(f"# OpenCourant Engine Input Deck\n")
            f.write(f"# Model: {self.title}\n")
            f.write(f"/RUN/{self.title[:20]}/1\n")
            f.write(f"{t_stop:16.6f}\n")
            f.write(f"/ANIM/DT\n")
            f.write(f"{anim_dt:16.6f}\n")
            f.write("/ANIM/SHELL/TENS/STRESS/ALL\n")
            f.write("/ANIM/BRICK/TENS/STRESS/ALL\n")
            f.write("/ANIM/ELEM/DAMAGE\n")
            f.write("/ANIM/ELEM/ENERGY\n")
            f.write("/ANIM/VECT/DISP\n")
            f.write("/ANIM/VECT/CONT\n")
            f.write(f"/TFILE\n")
            f.write(f"{th_dt:16.6f}\n")
            f.write("/TH/NODE/1\n")
            f.write("PUNCH_DISP_FORCE\n")
            f.write("         1         1         1         1\n")
            f.write("/ENG/MON/ON\n")
            f.write("/DT/NODA/CST\n")
            f.write("  0.900000        1.000000E-07\n") # Scale factor 0.9, min time step 1e-7 s
