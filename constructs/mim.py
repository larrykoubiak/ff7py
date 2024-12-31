from construct import Adapter, Array,BitsInteger,BitStruct, ByteSwapped, ExprAdapter, Flag, GreedyRange, Struct
from construct import Int8ul, Int16ul, Int32ul, this
from dataclasses import dataclass, field
from globals import lzs
from PIL import Image
from PIL import ImagePalette
from typing import List, Optional

@dataclass
class PaletteEntry:
    red: int
    green: int
    blue: int
    stp: bool

    def getColorData(self):
        return [self.red, self.green, self.blue]

@dataclass
class Palette:
    width: int
    entries: List[PaletteEntry]

    def getImagePalette(self):
        data  = [c for e in self.entries for c in e.getColorData() ]
        pal = ImagePalette.ImagePalette(mode="rgb", palette=data)
        return pal

    def getTransparenctyIndexes(self):
        indexes = [i for i in range(self.width) if self.entries[i].stp]
        return None if len(indexes) == 0 else indexes[0]

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
        self.tkimg = None

    @classmethod
    def from_file(cls, path: str):
        stream = lzs.un_lzs(path)
        mim = MIMConstruct.parse_stream(stream)
        return cls(mim.clut, mim.textures)

    def get_image_data(self, palette_id=0):
        if self.tkimg is None:
            pal = self.clut.palettes[palette_id].getImagePalette()
            img = Image.new(mode="RGBA",size=(1024,512),color=(0,0,0,255))
            for y in range(self.clut.height):
                for x in range(self.clut.width):
                    color = tuple(self.clut.palettes[y].entries[x].getColorData())
                    img.putpixel((self.clut.x + x, self.clut.y + y),color)
            for t in self.textures:
                data = bytes([byte for value in t.data for byte in value.to_bytes(2, byteorder='little')])
                ti = Image.frombytes(mode="P", size=(t.width*2,t.height),data=data)
                ti.putpalette(pal)
                transparency = self.clut.palettes[palette_id].getTransparenctyIndexes() or 0
                if transparency is not None:
                    ti.info["transparency"] = transparency
                overlay = ti.convert("RGBA")
                img.paste(overlay,(t.x*2, t.y), overlay)
            self.tkimg = img
        return self.tkimg

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
                            stp = e.stp > 0,
                            blue = (e.blue << 3) + (e.blue >> 2),
                            green = (e.green << 3) + (e.green >> 2),
                            red = (e.red << 3) + (e.red >> 2)
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

CLUTConstruct = CLUTAdapter(Struct(
    "length" / Int32ul,
    "x" / Int16ul,
    "y" / Int16ul,
    "width" / Int16ul,
    "height" / Int16ul,
    "palettes" / Array(
        this.height,
        "palette" / Array(
            this.width,
            "color"/ ByteSwapped(BitStruct(
                "stp" / BitsInteger(1),
                "blue" / BitsInteger(5),
                "green" / BitsInteger(5),
                "red" / BitsInteger(5),
            ))
        )
    )
))

TextureConstruct = TextureAdapter(Struct(
    "length" / Int32ul,
    "x" / Int16ul,
    "y" / Int16ul,
    "width" / Int16ul,
    "height" / Int16ul,
    "data" / Array(
        lambda ctx: ctx.width * ctx.height,
        Int16ul
    )
))

MIMConstruct = Struct(
    "clut" / CLUTConstruct,
    "textures" / GreedyRange(TextureConstruct)
)

CLUTConstruct.compile()
TextureConstruct.compile()
MIMConstruct.compile()