from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AKAOFrame:
    magic: str  # Assuming default value is "AKAO"
    id: int  # UInt16 equivalent in Python is just an integer, ensure it's within 0-65535
    length: int
    unknown: List[int] = field(default_factory=list)  # 4-byte array

    def __repr__(self):
        unknown_str = ' '.join(format(byte, '02X') for byte in self.unknown)
        return f"Magic: {self.magic}\nId: {self.id}\nLength: {self.length}\nUnknown: {unknown_str}"