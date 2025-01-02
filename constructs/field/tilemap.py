from construct import Adapter, Array, BitStruct, ByteSwapped, Computed, FixedSized, GreedyRange, IfThenElse, Padding, Pass, RepeatUntil, Struct, Tell
from construct import Int8ul, Int16ul, Int16sl, Int32ul, BitsInteger, this
from enum import IntEnum
from dataclasses import dataclass
from ..mim import MIM
from PIL import Image, ImagePalette, ImageChops
from typing import List

@dataclass
class TexturePageInfo:
    page_x: int
    page_y: int
    blending_mode: int
    depth: int

@dataclass
class TileInfo:
    pos: int
    type: int
    destination_x: int
    destination_y: int
    tex_page_source_x: int
    tex_page_source_y: int
    clut_number: int
    tp_blend: TexturePageInfo
    group: int
    parameter_blend: int
    parameter_id: int
    state: int

@dataclass
class Tilemap:
    origin_x: int
    origin_y: int
    width: int
    height: int
    background_tiles: List[TileInfo]
    texture_pages: List[TexturePageInfo]
    sprite_tiles: List[TileInfo]
    extra_tiles: List[TileInfo]

    def get_image_data(self, mim: MIM):
        img = Image.new(mode="RGBA",size=(self.width,self.height),color=(0,0,0,255))
        # draw background
        for t in self.background_tiles:
            tpi = t.tp_blend
            tileimg = mim.get_tile_data(t.clut_number, tpi.page_x, tpi.page_y, t.tex_page_source_x, t.tex_page_source_y)
            dest_x = t.destination_x - self.origin_x
            dest_y = t.destination_y - self.origin_y
            img.paste(tileimg,(dest_x,dest_y), tileimg)
        # draw sprites
        for t in self.sprite_tiles:
            tpi = t.tp_blend
            tileimg = mim.get_tile_data(t.clut_number, tpi.page_x, tpi.page_y, t.tex_page_source_x, t.tex_page_source_y)
            dest_x = t.destination_x - self.origin_x
            dest_y = t.destination_y - self.origin_y
            if t.parameter_blend == 1:
                src_tile = img.crop((dest_x, dest_y, dest_x + 16, dest_y + 16))
                if tpi.blending_mode in (1, 3):
                    blended = ImageChops.add(src_tile, tileimg)
                elif tpi.blending_mode == 2:
                    blended = ImageChops.subtract(src_tile, tileimg)
                img.paste(blended,(dest_x, dest_y))
                del src_tile
                del blended
            else:
                img.paste(tileimg,(dest_x,dest_y), tileimg)
            del tileimg
        return img

class TilemapAdapter(Adapter):
    def _decode(self, obj, context, path):
        min_x = min(
            min([b.destination_x for p in obj.background_tiles for b in p.tiles]),
            min([1 <<16] if len(obj.sprite_tiles) == 0 else [b.destination_x for p in obj.sprite_tiles for b in p.tiles]),
            min([1 <<16] if len(obj.extra_tiles) == 0 else [b.destination_x for p in obj.extra_tiles for b in p.tiles])
        )
        min_y = min(
            min([b.destination_y for p in obj.background_tiles for b in p.tiles]),
            min([1 <<16] if len(obj.sprite_tiles) == 0 else [b.destination_y for p in obj.sprite_tiles for b in p.tiles]),
            min([1 <<16] if len(obj.extra_tiles) == 0 else [b.destination_y for p in obj.extra_tiles for b in p.tiles])
        )
        max_x = max(
            max([b.destination_x for p in obj.background_tiles for b in p.tiles]),
            max([-1 <<16] if len(obj.sprite_tiles) == 0 else [b.destination_x for p in obj.sprite_tiles for b in p.tiles]),
            max([-1 <<16] if len(obj.extra_tiles) == 0 else [b.destination_x for p in obj.extra_tiles for b in p.tiles])
        )
        max_y = max(
            max([b.destination_y for p in obj.background_tiles for b in p.tiles]),
            max([-1 <<16] if len(obj.sprite_tiles) == 0 else [b.destination_y for p in obj.sprite_tiles for b in p.tiles]),
            max([-1 <<16] if len(obj.extra_tiles) == 0 else [b.destination_y for p in obj.extra_tiles for b in p.tiles])
        )

        texture_pages = [TexturePageInfo(tp.page_x,tp.page_y,tp.blending_mode, tp.depth) for tp in obj.texture_page_data]

        background_tiles = []
        page_tiles = []
        for p in obj.background_tiles:
            if p.info.type != 0x7FFE:
                page_tiles.extend([(p.info,t) for t in p.tiles])
            else:
                tp = texture_pages[p.info.pos]
                background_tiles.extend([
                    TileInfo(i.pos, i.type, t.destination_x, t.destination_y, t.tex_page_source_x, t.tex_page_source_y, t.tile_clut_data.clut_number,
                            obj.texture_page_data[p.info.pos],None, None,None, None)
                    for i, t in page_tiles
                ])
                page_tiles = []

        sprite_tiles = [
            TileInfo(p.info.pos, p.info.type, t.destination_x, t.destination_y, t.tex_page_source_x, t.tex_page_source_y, t.tile_clut_data.clut_number,
                    TexturePageInfo(
                        t.sprite_tp_blend.page_x,
                        t.sprite_tp_blend.page_y,
                        t.sprite_tp_blend.blending_mode, 
                        t.sprite_tp_blend.depth
                    ),
                    t.group, t.parameter.blending, t.parameter.param_id, t.state)
            for p in obj.sprite_tiles for t in p.tiles
        ]

        extra_tiles = []
        page_tiles = []
        for p in obj.extra_tiles:
            if p.info.type != 0x7FFE:
                page_tiles.extend([(p.info,t) for t in p.tiles])
            else:
                tp = texture_pages[p.info.pos]
                extra_tiles.extend([
                    TileInfo(i.pos, i.type, t.destination_x, t.destination_y, t.tex_page_source_x, t.tex_page_source_y, t.tile_clut_data.clut_number,
                            obj.texture_page_data[p.info.pos],None, t.parameter.blending, t.parameter.param_id, t.state)
                    for i, t in page_tiles
                ])
                page_tiles = []

        return Tilemap(min_x,min_y,(max_x - min_x + 16),(max_y - min_y + 16),background_tiles,texture_pages,sprite_tiles,extra_tiles)

CLUTDataConstruct = ByteSwapped(
    BitStruct(
        Padding(6),
        "clut_number" / BitsInteger(4),
        Padding(6)
    )
)

SpriteTPBlendConstruct = ByteSwapped(
    BitStruct(
        Padding(7),
        "depth" / BitsInteger(2),
        "blending_mode" / BitsInteger(2),
        "page_y" / BitsInteger(1),
        "page_x" / BitsInteger(4)
    )
)

ParameterConstruct = BitStruct(
    "blending" / BitsInteger(1),
    "param_id" / BitsInteger(7)
)

TilemapConstruct = TilemapAdapter(Struct(
    "start" / Tell,
    "background_info_offset" / Int32ul,
    "texture_page_offset" / Int32ul,
    "sprite_info_offset" / Int32ul,
    "extra_info_offset" / Int32ul,
    "layer_infos" / Array(
        4,
        RepeatUntil(
            lambda obj, lst, ctx: obj.type == 0x7FFF,
            Struct(
                "type" / Int16ul,
                "pos" / IfThenElse(lambda ctx: ctx.type == 0x7FFF,Pass,Int16ul),
                "count" / IfThenElse(lambda ctx: ctx.type == 0x7FFF,Pass,Int16ul)
            )
        )
    ),
    "background_tiles" / Array(
        lambda ctx: len(ctx.layer_infos[0]) - 1,
        Struct(
            "info" / Computed(lambda ctx: ctx._.layer_infos[0][ctx._index]),
            "tiles" / Array(
                lambda ctx: ctx.info.count,
                Struct(
                    "destination_x" / Int16sl,
                    "destination_y" / Int16sl,
                    "tex_page_source_x" / Int8ul,
                    "tex_page_source_y" / Int8ul,
                    "tile_clut_data" / CLUTDataConstruct
                )
            )
        )
    ),
    "texture_page_data" / FixedSized(
        lambda ctx: ctx.sprite_info_offset - ctx.texture_page_offset,
        GreedyRange(SpriteTPBlendConstruct)
    ),
    "sprite_tiles" / Array(
        lambda ctx: len(ctx.layer_infos[1]) - 1,
        Struct(
            "info" / Computed(lambda ctx: ctx._.layer_infos[1][ctx._index]),
            "tiles" / Array(
                lambda ctx: ctx.info.count,
                Struct(
                    "destination_x" / Int16sl,
                    "destination_y" / Int16sl,
                    "tex_page_source_x" / Int8ul,
                    "tex_page_source_y" / Int8ul,
                    "tile_clut_data" / CLUTDataConstruct,
                    "sprite_tp_blend" / SpriteTPBlendConstruct,
                    "group" / Int16ul,
                    "parameter" / ParameterConstruct,
                    "state" / Int8ul
                )
            )
        )
    ),
    "extra_tiles" / Array(
        lambda ctx: len(ctx.layer_infos[2]) - 1,
        Struct(
            "info" / Computed(lambda ctx: ctx._.layer_infos[2][ctx._index]),
            "tiles" / Array(
                lambda ctx: ctx.info.count,
                Struct(
                    "destination_x" / Int16sl,
                    "destination_y" / Int16sl,
                    "tex_page_source_x" / Int8ul,
                    "tex_page_source_y" / Int8ul,
                    "tile_clut_data" / CLUTDataConstruct,
                    "parameter" / ParameterConstruct,
                    "state" / Int8ul
                )
            )
        )
    )
))