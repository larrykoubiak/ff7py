from copy import deepcopy
from dataclasses import asdict
from globals import opcodes
from structs.opcode import Opcode, Operand
from io import BytesIO
from struct import unpack
from structs.akao import AKAOFrame
from structs.entity import Entity, EntityScript
from utils.bitreader import BitReader
from utils.ff7text import FF7Text
class Script:
    def __init__(self, data = None):
        self.scale = 0
        self.creator = ''
        self.name = ''
        self.entities = []
        self.dialogs = []
        self.akaos = []
        if data is not None:
            self.read(data)

    def read(self, data):
        self.stream = BytesIO(data)
        # Read header
        _, nb_entities, nb_models = unpack('<HBB', self.stream.read(4))
        string_offset = unpack('<H', self.stream.read(2))[0]
        nb_akao_offsets = unpack('<H', self.stream.read(2))[0]
        self.scale = unpack('<H', self.stream.read(2))[0]
        self.stream.read(6)
        self.creator = self.stream.read(8).decode('ascii').strip('\x00')
        self.name = self.stream.read(8).decode('ascii').strip('\x00')
        # Entities
        self.entities = [Entity(name=self.stream.read(8).decode('ascii').strip('\x00')) for _ in range(nb_entities)]
        akao_offsets = [unpack('<I', self.stream.read(4))[0] for _ in range(nb_akao_offsets)]
        entity_offsets = [[unpack('<H', self.stream.read(2))[0] for _ in range(32)] for _ in range(nb_entities)]
        # Dialogs
        self.stream.seek(string_offset, 0)
        nb_dialogs = unpack('<H', self.stream.read(2))[0]
        dialog_offsets = [unpack('<H', self.stream.read(2))[0] + string_offset for _ in range(nb_dialogs)]
        dialog_offsets.append(len(data) if nb_akao_offsets == 0 else akao_offsets[0])
        for i in range(nb_dialogs):
            size = dialog_offsets[i+1] - dialog_offsets[i]
            self.stream.seek(dialog_offsets[i], 0)
            dialogdata = self.stream.read(size)
            dialogtext = FF7Text.decode_bytes(dialogdata, size)
            self.dialogs.append(dialogtext)
        # Entity scripts
        for i in range(nb_entities):
            entity = self.entities[i]
            entity.scripts = []
            for j in range(32):
                entityscript = EntityScript(address=entity_offsets[i][j])
                self.stream.seek(entity_offsets[i][j], 0)
                while True:
                    code = self.stream.read(1)[0]
                    op: Opcode = deepcopy(opcodes[code])
                    if op.size > 0:
                        operand_data = self.stream.read((op.size // 8))
                        breader = BitReader(operand_data)
                        for o in op.operands:
                            operand: Operand = o
                            operand.value = breader.read(operand.size)
                    entityscript.opcodes.append(op)
                    if code == 0:
                        break
                entity.scripts.append(entityscript)
        # AKAO
        for i in range(nb_akao_offsets):
            self.stream.seek(akao_offsets[i], 0)
            magic = self.stream.read(4).decode('ascii').strip('\x00')
            id, length = unpack('<HH', self.stream.read(4))
            unknown = unpack('<8B', self.stream.read(8))
            self.akaos.append(AKAOFrame(magic, id, length, unknown))

    def to_dict(self):
        return {
            "name": self.name,
            "creator": self.creator,
            "scale": self.scale,
            "entities": {
                e.name: {
                    es.address:
                    {
                        o.name: {
                            op.name: op.value for op in o.operands
                        } for o in es.opcodes
                    } for es in e.scripts
                }
                for e in self.entities
            },
            "dialogs": [d for d in self.dialogs],
            "akaos": [asdict(a) for a in self.akaos],
        }

    def __repr__(self) -> str:
        return f"{self.name} (by {self.creator}) scale: {self.scale}"

