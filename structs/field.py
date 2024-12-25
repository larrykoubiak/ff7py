from enum import IntEnum
from globals import lzs
from struct import unpack
from structs.script import Script

class Offset(IntEnum):
    SCRIPT = 0
    WALKMESH = 1
    TILEMAP = 2
    CAMERA_MATRIX = 3
    TRIGGERS = 4
    ENCOUNTER = 5
    MODEL = 6

class Field:
    def __init__(self, filename=None):
        self.stream = None
        self.offsets = [0] * 7
        self.script = None
        self.walkmesh = None
        self.tile_map = None
        if filename is not None:
            self.read(filename)

    def read(self, filename):
        # Parse file
        self.stream = lzs.un_lzs(filename)
        self.read_offsets()
        self.script = Script(self.get_offset_data(Offset.SCRIPT))
        # self.walkmesh = self.read_walkmesh(self.offsets[Offset.WALKMESH.value], self.offsets[Offset.TILEMAP.value])
        # self.tile_map = self.read_tilemap(self.offsets[Offset.TILEMAP.value], self.offsets[Offset.CAMERA_MATRIX.value])
        # Cleanup
        self.stream.close()
        return self

    def read_offsets(self):
        buff = 0
        memory_offset = 0
        self.stream.seek(0)  # Move to the beginning of the stream
        for i in range(7):
            buff, = unpack('I', self.stream.read(4))
            if memory_offset == 0:
                memory_offset = buff
            self.offsets[i] = (buff - memory_offset + 28)

    def get_offset_data(self, offset: Offset):
        size = self.offsets[offset + 1] - self.offsets[offset]
        self.stream.seek(self.offsets[offset])
        data = self.stream.read(size)
        return data

    def dump(self):
        dic = {
            "script": self.script.to_dict()
        }
        return dic