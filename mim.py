from construct import Adapter, Array,BitsInteger,BitStruct, Bytes, ExprAdapter, Flag, GreedyRange, Struct
from construct import Int8ul, Int16ul, Int32ul, this
from dataclasses import dataclass, field
from globals import lzs
from PIL.Image import Image
from PIL.ImagePalette import ImagePalette
from typing import List, Optional

@dataclass
class PaletteEntry:
    red: int
    green: int
    blue: int
    stp: int

    def getColorData(self):
        return [self.red, self.green, self.blue]

@dataclass
class Palette:
    width: int
    entries: List[PaletteEntry]

    def getImagePalette(self):
        return ImagePalette(mode="rgb", palette=[e.getColorData for e in self.entries])

@dataclass
class CLUT:
    x: int
    y: int
    width: int
    height: int
    palettes: List[Palette]

@dataclass
class Texture:
    x: int
    y: int
    width: int
    height: int
    data: List[int]

class MIM:
    def __init__(self, clut: CLUT, textures: List[Texture]):
        self.clut = clut
        self.textures= textures

    @classmethod
    def from_file(cls, path: str):
        stream = lzs.un_lzs(path)
        mim = MIMStruct.parse_stream(stream)
        return cls(mim.clut, mim.textures)

    def show_image(self, paletteId=0):
        palette = self.clut.palettes[paletteId].getImagePalette()


class CLUTAdapter(Adapter):
    def _decode(self, obj, context, path):
        return CLUT(
            x=obj.x,
            y=obj.y,
            width=obj.width,
            height=obj.height,
            palettes=[
                Palette(
                    width=obj.width,
                    entries=[
                        PaletteEntry(
                            red=e.red,
                            green=e.green,
                            blue=e.blue,
                            stp=e.stp
                        ) for e in p
                    ]
                ) for p in obj.palettes
            ]
        )

class TextureAdapter(Adapter):
    def _decode(self, obj, context, path):
        return Texture(
            x=obj.x,
            y=obj.y,
            width=obj.width,
            height=obj.height,
            data=obj.data
        )

CLUTStruct = CLUTAdapter(Struct(
    "length" / Int32ul,
    "x" / Int16ul,
    "y" / Int16ul,
    "width" / Int16ul,
    "height" / Int16ul,
    "palettes" / Array(
        this.height,
        "palette" / Array(
            this.width,
            "color" / BitStruct(
                "red" / BitsInteger(5),
                "green" / BitsInteger(5),
                "blue" / BitsInteger(5),
                "stp" / Flag
            )
        )
    )
))

TextureStruct = TextureAdapter(Struct(
    "length" / Int32ul,
    "x" / Int16ul,
    "y" / Int16ul,
    "width" / ExprAdapter(
        Int16ul,
        lambda obj, ctx: obj * 2,
        lambda obj, ctx: obj / 2
    ),
    "height" / Int16ul,
    "data" / Bytes(this.width)
))

MIMStruct = Struct(
    "clut" / CLUTStruct,
    "textures" / GreedyRange(TextureStruct)
)

if __name__ == '__main__':
    m = MIM.from_file(r'D:\PS1\ff7\FIELD\4SBWY_1.MIM')
    print(m.textures)