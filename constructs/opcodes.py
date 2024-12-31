from construct import Adapter, BitStruct, BitsInteger, Byte, Bytes, Bytewise, Computed, ExprAdapter, Struct
from construct import Int8ul, Int8sl, Int16ul, Int16sl, Int32ul, Int32sl, this
from copy import deepcopy
from dataclasses import dataclass, field
from json import load
from typing import List, Optional

@dataclass
class Operand:
    name: str = ''
    description: str = ''
    size: str = ''
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
    bitstruct: BitStruct = field(init=False)

    def __post_init__(self):
        objlist = [Operand(**operand) if isinstance(operand, dict) else operand for operand in self.operands]
        self.operands = objlist[:]
        fields = [(o.name / eval(o.size)) for o in self.operands]
        if fields:
            self.bitstruct = BitStruct(*fields)
            self.bitstruct.compile()
        else:
            self.bitstruct = BitStruct()

    @property
    def size(self) -> int:
        return 0 if self.bitstruct is None else self.bitstruct.sizeof()

    def __repr__(self) -> str:
        str_repr = f"{self.longname} "
        if self.operands:
            operand_strs = ', '.join(str(operand) for operand in self.operands)
            str_repr += f"({operand_strs})"
        return str_repr

class FieldOpcodeAdapter(Adapter):
    def _decode(self, obj, context, path):
        opcode: Opcode = deepcopy(fieldOpcodes[obj.opcode])
        for op in opcode.operands:
            op.value = obj.operands[op.name]
        return opcode

class AKAOOpcodeAdapter(Adapter):
    def _decode(self, obj, context, path):
        opcode: Opcode = deepcopy(akaoOpcodes[obj.opcode])
        for op in opcode.operands:
            op.value = obj.operands[op.name]
        return opcode

FieldOpcodeConstruct = FieldOpcodeAdapter(
    Struct(
        "opcode" / Byte,
        "mnemonic" / Computed(lambda this: fieldOpcodes[this.opcode].name),
        "operands" / ExprAdapter(
            Bytes(lambda ctx: fieldOpcodes[ctx.opcode].size),
            decoder = lambda raw, ctx: fieldOpcodes[ctx.opcode].bitstruct.parse(raw),
            encoder= lambda obj, ctx: fieldOpcodes[ctx.opcode].bitstruct.build(obj)
        )
    )
)

AKAOOpcodeConstruct = AKAOOpcodeAdapter(
    Struct(
        "opcode" / Byte,
        "mnemonic" / Computed(lambda this: akaoOpcodes[this.opcode].name),
        "operands" / ExprAdapter(
            Bytes(lambda ctx: akaoOpcodes[ctx.opcode].size),
            decoder = lambda raw, ctx: akaoOpcodes[ctx.opcode].bitstruct.parse(raw),
            encoder= lambda obj, ctx: akaoOpcodes[ctx.opcode].bitstruct.build(obj)
        )
    )
)

FieldOpcodeConstruct.compile()
AKAOOpcodeConstruct.compile()

with open("FieldScriptOpcodes.json", "r", encoding="utf-8") as f:
    _fieldopcodes = load(f)
fieldOpcodes = []
for opcodedict in _fieldopcodes:
    opcode = Opcode(**opcodedict)
    fieldOpcodes.append(opcode)

with open("AKAOOpcodes.json", "r", encoding="utf-8") as f:
    _akaoopcodes = load(f)
akaoOpcodes = []
for opcodedict in _akaoopcodes:
    opcode = Opcode(**opcodedict)
    akaoOpcodes.append(opcode)