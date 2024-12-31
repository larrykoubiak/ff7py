from construct import Padding, Peek, Pointer, Struct
from construct import Int32ul, this
from .script import ScriptConstruct
from .walkmesh import WalkmeshConstruct
from .camera import CameraConstruct
from .tilemap import TilemapConstruct
from globals import lzs

class Field:
    def __init__(self, script=None, walkmesh=None, tilemap=None, camera=None):
        self.script = script
        self.walkmesh = walkmesh
        self.tilemap = tilemap
        self.camera = camera

    @classmethod
    def from_file(cls, path: str):
        stream = lzs.un_lzs(path)
        field = FieldConstruct.parse_stream(stream)
        return cls(script=field.script,walkmesh=field.walkmesh, tilemap=field.tilemap, camera=field.camera)

FieldConstruct = Struct(
    "first_offset" / Peek(Int32ul),
    "script_offset_psx" / Int32ul,
    "script" / Pointer(
        this.script_offset_psx - this.first_offset + 28,
        ScriptConstruct
    ),
    "walkmesh_offset_psx" / Int32ul,
    "walkmesh" / Pointer(
        this.walkmesh_offset_psx - this.first_offset + 28,
        WalkmeshConstruct
    ),
    "tilemap_offset_psx" / Int32ul,
    "tilemap" / Pointer(
        this.tilemap_offset_psx - this.first_offset + 28,
        TilemapConstruct
    ),
    "camera_offset_psx" / Int32ul,
    "camera" / Pointer(
        this.camera_offset_psx - this.first_offset + 28,
        CameraConstruct
    )
)