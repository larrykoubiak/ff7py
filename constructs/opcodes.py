from construct import (
    Adapter, BitStruct, BitsInteger, Byte, Bytewise, Bytes, Computed, ExprAdapter, Struct
)
from construct import Int8ul, Int8sl, Int16ul, Int16sl, Int32ul, Int32sl, this
from dataclasses import dataclass, field
from json import load
from typing import List, Optional

@dataclass
class OperandTemplate:
    name: str
    description: str
    size: str

@dataclass
class OpcodeTemplate:
    id: int
    name: str
    longname: str
    description: str
    operands: List[OperandTemplate] = field(default_factory=list)
    bitstruct: BitStruct = field(init=False, repr=False)

    def __post_init__(self):
        # Build a BitStruct from the operand templates
        if self.operands:
            fields = []
            for op in self.operands:
                # Use eval to turn "BitsInteger(8)" into an actual construct
                fields.append(op.name / eval(op.size))
            self.bitstruct = BitStruct(*fields)
            self.bitstruct.compile()
        else:
            self.bitstruct = BitStruct()

    @property
    def size(self) -> int:
        # bitstruct.sizeof() returns bits, so that's what
        # the code is using in your original snippet
        return self.bitstruct.sizeof() if self.bitstruct else 0

    def __repr__(self) -> str:
        return f"{self.longname} (template)"


@dataclass
class Operand:
    name: str
    description: str
    size: str
    value: Optional[str] = None

    def __repr__(self) -> str:
        return f"{self.name}:={self.value}"

@dataclass
class Opcode:
    id: int
    name: str
    longname: str
    description: str
    operands: List[Operand] = field(default_factory=list)
    bitstruct: BitStruct = None

    def __repr__(self) -> str:
        if self.operands:
            operand_strs = ', '.join(str(o) for o in self.operands)
            return f"{self.longname} ({operand_strs})"
        return self.longname


def create_runtime_opcode(template: OpcodeTemplate, operand_values: dict) -> Opcode:
    """
    Build a new Opcode instance from a template plus a dict of operand values.
    """
    # 1) Copy only what we need from the template
    runtime_operands = []
    for op_tmpl in template.operands:
        val = operand_values.get(op_tmpl.name, None)
        runtime_operands.append(
            Operand(
                name=op_tmpl.name,
                description=op_tmpl.description,
                size=op_tmpl.size,
                value=val,
            )
        )

    # 2) Construct a brand new Opcode
    return Opcode(
        id=template.id,
        name=template.name,
        longname=template.longname,
        description=template.description,
        operands=runtime_operands,
        bitstruct=template.bitstruct,   # point to the same compiled struct
    )


class FieldOpcodeAdapter(Adapter):
    def _decode(self, obj, context, path):
        template_opcode = fieldOpcodes[obj.opcode]
        return create_runtime_opcode(template_opcode, obj.operands)

class AKAOOpcodeAdapter(Adapter):
    def _decode(self, obj, context, path):
        template_opcode = akaoOpcodes[obj.opcode]
        return create_runtime_opcode(template_opcode, obj.operands)


FieldOpcodeConstruct = FieldOpcodeAdapter(
    Struct(
        "opcode" / Byte,
        "mnemonic" / Computed(lambda ctx: fieldOpcodes[ctx.opcode].name),
        "operands" / ExprAdapter(
            Bytes(lambda ctx: fieldOpcodes[ctx.opcode].size),
            decoder=lambda raw, ctx: fieldOpcodes[ctx.opcode].bitstruct.parse(raw),
            encoder=lambda obj, ctx: fieldOpcodes[ctx.opcode].bitstruct.build(obj),
        )
    )
)

AKAOOpcodeConstruct = AKAOOpcodeAdapter(
    Struct(
        "opcode" / Byte,
        "mnemonic" / Computed(lambda ctx: akaoOpcodes[ctx.opcode].name),
        "operands" / ExprAdapter(
            Bytes(lambda ctx: akaoOpcodes[ctx.opcode].size),
            decoder=lambda raw, ctx: akaoOpcodes[ctx.opcode].bitstruct.parse(raw),
            encoder=lambda obj, ctx: akaoOpcodes[ctx.opcode].bitstruct.build(obj),
        )
    )
)

FieldOpcodeConstruct.compile()
AKAOOpcodeConstruct.compile()


def load_opcodes_from_json(path) -> List[OpcodeTemplate]:
    """Parses a JSON array of opcode objects into a list of OpcodeTemplate."""
    with open(path, "r", encoding="utf-8") as f:
        data = load(f)

    templates = []
    for item in data:
        operand_templates = []
        for op_def in item.get("operands", []):
            operand_templates.append(
                OperandTemplate(
                    name=op_def["name"],
                    description=op_def.get("description", ""),
                    size=op_def["size"]
                )
            )
        opcode_template = OpcodeTemplate(
            id=item["id"],
            name=item["name"],
            longname=item.get("longname", ""),
            description=item.get("description", ""),
            operands=operand_templates,
        )
        templates.append(opcode_template)
    return templates


fieldOpcodes = load_opcodes_from_json("FieldScriptOpcodes.json")
akaoOpcodes  = load_opcodes_from_json("AKAOOpcodes.json")