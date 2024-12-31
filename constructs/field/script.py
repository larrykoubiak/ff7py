from construct import Adapter, Array,Byte, ExprAdapter, Padding, PaddedString, Pointer, RepeatUntil, Struct, Tell
from construct import Int8ul, Int16ul, Int32ul, this
from ..akao import AKAO, AKAOConstruct
from ..opcodes import Opcode, FieldOpcodeConstruct
from dataclasses import dataclass
from typing import List
from utils.ff7text import FF7Text

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
    akaos: List[AKAO]
    entities: List[Entity]
    dialogs: List[str]

class ScriptAdapter(Adapter):
    def _decode(self, obj, context, path):
        return Script(
            scale= obj.scale,
            creator = obj.creator,
            name = obj.name,
            akaos = [a.AKAO for a in obj.akaos],
            entities= [
                Entity(
                    name=obj.entities[i],
                    scripts=[EntityScript(s.offset, s.instructions) for s in obj.entityScripts[i]]
                ) 
                for i in range(obj.nbEntities)
            ],
            dialogs=[
                e for e in obj.dialogs.entries
            ]
        )

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
    "akaos" / Array(
        this.nbAKAOOffsets,
        Struct(
            "offset" / Int32ul,
            "AKAO" / Pointer(lambda ctx: ctx.offset + ctx._.start,AKAOConstruct)
        )
    ),
    "entityScripts" / Array(
        this.nbEntities, Array(
            32,
            Struct(
                "offset" / Int16ul,
                "instructions" / Pointer(
                    lambda ctx: ctx.offset + ctx._.start,
                    RepeatUntil(lambda obj, lst, ctx: obj.id == 0, FieldOpcodeConstruct)
                )
            )
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

ScriptConstruct.compile()