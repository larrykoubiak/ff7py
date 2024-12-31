from dataclasses import dataclass
from utils.lzs import LZS

lzs = LZS()

@dataclass
class Vertex3:
    x: int
    y: int
    z: int