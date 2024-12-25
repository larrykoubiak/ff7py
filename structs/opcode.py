from dataclasses import dataclass, field
from typing import List, Optional

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
        # Convert operand dictionaries to Operand instances
        objlist = [Operand(**operand) if isinstance(operand, dict) else operand for operand in self.operands]
        self.operands = objlist[:]

    @property
    def size(self) -> int:
        return sum(operand.size for operand in self.operands)

    def __repr__(self) -> str:
        str_repr = f"{self.name} "
        if self.operands:
            operand_strs = ', '.join(str(operand) for operand in self.operands)
            str_repr += f"({operand_strs})"
        return str_repr
