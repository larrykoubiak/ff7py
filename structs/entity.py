from dataclasses import dataclass, field
from typing import List, Optional
from structs.opcode import Opcode

@dataclass
class EntityScript:
    address: int
    opcodes: List[Opcode] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Script [0x{self.address:04X}]"

@dataclass
class Entity:
    name: str
    scripts: List[EntityScript] = field(default_factory=list)

    def unique_scripts(self):
        return 

    def __repr__(self) -> str:
        return self.name