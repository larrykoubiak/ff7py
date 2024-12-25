from structs.opcode import Opcode, Operand
from json import load
from utils.lzs import LZS

with open("FieldScriptOpcodes.json", "r", encoding="utf-8") as f:
    _opcodeslist = load(f)
opcodes = []
for opcodedict in _opcodeslist:
    opcode = Opcode(**opcodedict)
    opcodes.append(opcode)
lzs = LZS()