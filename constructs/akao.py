from construct import Adapter, Array, BitsInteger, BitStruct, Byte, Computed, Const, ExprAdapter, Padding, RepeatUntil, Pointer, Struct, Tell
from construct import Int8ul, Int16ul, Int24ul, Int32ul, this
from constructs.opcodes import Opcode, AKAOOpcodeConstruct
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class AKAOScript:
    address: int
    instructions: List[Opcode]

@dataclass
class AKAO:
    id: int
    length: int
    reverb_type: int
    timestamp: datetime
    mask: str
    nb_channels: int
    scripts: List[AKAOScript]

class AKAOAdapter(Adapter):
    def _decode(self, obj, context, path):
        return AKAO(
            id=obj.id,
            length=obj.length,
            reverb_type=obj.reverb_type,
            timestamp=obj.timestamp,
            mask=bin(obj.mask)[2:],
            nb_channels=obj.num_channels,
            scripts=[AKAOScript(s.offset, s.instructions) for s in obj.scripts]
        )

class AKAOTimestampAdapter(Adapter):
    def _decode(self, obj, context, path):
        return datetime(
            year=obj.year,
            month=obj.month,
            day=obj.day,
            hour=obj.hour,
            minute=obj.minute,
            second=obj.second
        )

BCD = ExprAdapter(
    Byte,
    lambda obj, ctx: (obj >> 4) * 10 + (obj & 0x0F),
    lambda obj, ctx: ((obj // 10) << 4) | (obj % 10)
)

AKAOTimestamp = AKAOTimestampAdapter(Struct(
    "year" / BCD,
    "month" / BCD,
    "day" / BCD,
    "hour" / BCD,
    "minute" / BCD,
    "second" / BCD
))

AKAOConstruct = AKAOAdapter(Struct(
    "magic" / Const(b"AKAO"),
    "id" / Int16ul,
    "length" / Int16ul,
    "reverb_type" / Int16ul,
    "timestamp" / AKAOTimestamp,
    "mask" / Int24ul,
    Padding(1),
    "num_channels" / Computed(lambda ctx: bin(ctx.mask).count('1')),
    "scripts" / Array(
        lambda ctx: ctx.num_channels,
        Struct(
            "offset" / Int16ul,
            "currentPos" / Tell,
            "instructions" / Pointer(
                lambda ctx: ctx.currentPos + ctx.offset,
                RepeatUntil(lambda obj, lst, ctx: obj.id == 0xEE, AKAOOpcodeConstruct)
            )
        )
    )
))

AKAOTimestamp.compile()
AKAOConstruct.compile()