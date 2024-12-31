from construct import Adapter, Array, Padding, Struct
from construct import Int16ul, Int16sl, Int32ul, this
from dataclasses import dataclass
from globals import Vertex3
from typing import List

@dataclass
class Access:
    vertex1: Vertex3
    vertex2: Vertex3
    triangle_id: int

@dataclass
class Triangle:
    id: int
    vertices: List[Vertex3]
    access: List[Access]

@dataclass
class Walkmesh:
    nb_sectors: int
    triangles: List[Triangle]

class WalkmeshAdapter(Adapter):
    def _decode(self, obj, context, path):
        triangles = []
        for i in range(obj.nb_sectors):
            vertices = [Vertex3(x = t.x, y=t.y, z=t.z) for t in obj.sector_pool[i]]
            access = [
                Access(vertices[0], vertices[1],obj.access_pool[i].access1),
                Access(vertices[1], vertices[2],obj.access_pool[i].access2),
                Access(vertices[2], vertices[0],obj.access_pool[i].access3)
            ]
            triangles.append(Triangle(id=i, vertices=vertices, access=access))
        return Walkmesh(
            nb_sectors=obj.nb_sectors,
            triangles=triangles
        )

WalkmeshConstruct = WalkmeshAdapter(Struct(
    "nb_sectors" / Int32ul,
    "sector_pool" / Array(
        this.nb_sectors,
        "triangle" / Array(
            3,
            Struct(
                "x" / Int16sl,
                "y" / Int16sl,
                "z" / Int16sl,
                Padding(2)
            )
        )
    ),
    "access_pool" / Array(
        this.nb_sectors,
        Struct(
            "access1" / Int16ul,
            "access2" / Int16ul,
            "access3" / Int16ul
        )
    )
))

WalkmeshConstruct.compile()