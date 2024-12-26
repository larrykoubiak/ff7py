from construct import Adapter, Array,BitsInteger,BitStruct, Byte, Bytes, Computed, ExprAdapter, Padding, PaddedString, Pointer, RepeatUntil, Struct, Tell
from construct import Int8ul, Int16ul, Int32ul, this
from dataclasses import dataclass, field
from enum import IntEnum
from json import load
from typing import List, Optional
from globals import lzs
from utils.ff7text import FF7Text

class FieldOffset(IntEnum):
    SCRIPT = 0
    WALKMESH = 1
    TILEMAP = 2
    CAMERA_MATRIX = 3
    TRIGGERS = 4
    ENCOUNTER = 5
    MODEL = 6

@dataclass
class Operand:
    name: str = ''
    description: str = ''
    size: int = 0
    value: Optional[str] = None

    def __repr__(self) -> str:
        return f"{self.name}:={self.value}"

@dataclass
class Opcode:
    id: int = 0
    name: str = ''
    longname: str = ''
    description: str = ''
    operands: List[Operand] = field(default_factory=list)

    def __post_init__(self):
        objlist = [Operand(**operand) if isinstance(operand, dict) else operand for operand in self.operands]
        self.operands = objlist[:]

    @property
    def size(self) -> int:
        return sum(operand.size for operand in self.operands)

    @property
    def bitstruct(self):
        fields = [(o.name / BitsInteger(o.size)) for o in self.operands]
        return BitStruct(*fields)

    def __repr__(self) -> str:
        str_repr = f"{self.name} "
        if self.operands:
            operand_strs = ', '.join(str(operand) for operand in self.operands)
            str_repr += f"({operand_strs})"
        return str_repr

@dataclass
class EntityScript:
    address: int
    instructions: List[Opcode]

@dataclass
class Entity:
    name: str
    scripts: List[EntityScript]

@dataclass
class Script:
    scale: int
    creator: str
    name: str
    entities: List[str]
    dialogs: List[str]

class EntityScriptAdapter(Adapter):
    def _decode(self, obj, context, path):
        return EntityScript(
            address=obj.offset,
            instructions=[
                Opcode(
                    id = opcodes[o.opcode].id,
                    name = opcodes[o.opcode].name,
                    longname= opcodes[o.opcode].longname,
                    description=opcodes[o.opcode].description,
                    operands=[
                        Operand(
                            name=opcodes[o.opcode].operands[i].name,
                            description=opcodes[o.opcode].operands[i].description,
                            size=opcodes[o.opcode].operands[i].size,
                            value=o.operands[opcodes[o.opcode].operands[i].name]
                        ) for i in range(len(opcodes[o.opcode].operands))
                    ]
                ) for o in obj.entries
            ]
        )

class ScriptAdapter(Adapter):
    def _decode(self, obj, context, path):
        return Script(
            scale= obj.scale,
            creator = obj.creator,
            name = obj.name,
            entities= [
                Entity(
                    name=obj.entities[i],
                    scripts=obj.entityScripts[i]
                ) 
                for i in range(obj.nbEntities)
            ],
            dialogs=[
                e for e in obj.dialogs.entries
            ]
        )

class Field:
    def __init__(self, offsets: List[int], script=Script, walkmesh=None, tilemap=None):
        self.offsets = offsets
        self.script = script
        self.walkmesh = walkmesh
        self.tilemap = tilemap

    @classmethod
    def from_file(cls, path: str):
        stream = lzs.un_lzs(path)
        field = FieldConstruct.parse_stream(stream)
        return cls(field.offsets, script=field.script)

EntityScriptConstruct = EntityScriptAdapter(Struct(
    "offset" / Int16ul,
    "entries" / Pointer(
        lambda ctx: ctx.offset + 28,
        RepeatUntil(
            lambda instr, lst, ctx: instr.opcode == 0,
            Struct(
                "opcode" / Byte,
                "mnemonic" / Computed(lambda this: opcodes[this.opcode].name),
                "operands" / ExprAdapter(
                    Bytes(lambda ctx: opcodes[ctx.opcode].size >> 3),
                    decoder = lambda raw, ctx: opcodes[ctx.opcode].bitstruct.parse(raw),
                    encoder= lambda obj, ctx: opcodes[ctx.opcode].bitstruct.build(obj)
                )
            )
        )
    )
))

ScriptConstruct = ScriptAdapter(Struct(
    "start" / Tell,
    Padding(2),
    "nbEntities" / Int8ul,
    "nbModels" / Int8ul,
    "dialogsOffset" / Int16ul,
    "nbAKAOOffsets" / Int16ul,
    "scale" / Int16ul,
    Padding(6),
    "creator" / PaddedString(8, 'ascii'),
    "name" / PaddedString(8, 'ascii'),
    "entities" / Array(
        this.nbEntities,
        PaddedString(8, 'ascii')
    ),
    "akaoOffsets" / Array(
        this.nbAKAOOffsets,
        Int32ul
    ),
    "entityScripts" / Array(
        this.nbEntities, Array(
            32,
            EntityScriptConstruct
        )
    ),
    "dialogs" / Pointer(
        lambda ctx: ctx.dialogsOffset + ctx.start,
        Struct(
            "dialogstart" / Tell,
            "nbDialogs" / Int16ul,
            "dialogOffsets" / Array(
                this.nbDialogs,
                Int16ul
            ),
            "entries" / Array(
                this.nbDialogs,
                Pointer(
                    lambda ctx: ctx.dialogOffsets[ctx._index] + ctx._.dialogsOffset + ctx._.start,
                    "dialog" / ExprAdapter(
                        RepeatUntil(lambda byte, lst, ctx: byte == 0xFF, Byte),
                        decoder=lambda raw_list, ctx: FF7Text.decode_bytes(raw_list, len(raw_list)),
                        encoder=None
                    )
                )
            )
        )
    )
))

FieldConstruct = Struct(
    "offsets" / Array(7, Int32ul),
    "script"/ ScriptConstruct
)

with open("FieldScriptOpcodes.json", "r", encoding="utf-8") as f:
    _opcodeslist = load(f)
opcodes = []
for opcodedict in _opcodeslist:
    opcode = Opcode(**opcodedict)
    opcodes.append(opcode)

if __name__ == '__main__':
    f = Field.from_file("D:\\Temp\\Backup PSX\\ff7\\FIELD\\4SBWY_1.DAT")
    print(f.script)
