from construct import Adapter, Array, BitStruct, ByteSwapped, Computed, FixedSized, GreedyRange, IfThenElse, Padding, Pass, RepeatUntil, Struct, Tell
from construct import Int8ul, Int16ul, Int16sl, Int32ul, BitsInteger, this
from enum import IntEnum
from dataclasses import dataclass
from typing import List

class LayerType(IntEnum):
    BACKGROUND = 0
    SPRITE = 1
    EXTRA = 2
    UNKNOWN = 3

@dataclass
class TexturePageInfo:
    page_x: int
    page_y: int
    blending_mode: int
    depth: int

@dataclass
class TileInfo:
    destination_x: int
    destination_y: int
    tex_page_source_x: int
    tex_page_source_y: int
    tile_clut_data: int

@dataclass
class SpriteTileInfo(TileInfo):
    tp_blend: TexturePageInfo
    group: int
    parameter: 0
    state: 0

@dataclass
class LayerInfo:
    layer_info_type: int
    tile_pos: int
    tile_count: int
    tiles: List[TileInfo]

@dataclass
class LayerPage:
    page_id: int
    layer_infos: List[LayerInfo]

@dataclass
class Layer:
    layer_type: LayerType
    pages: List[LayerPage]

@dataclass
class Tilemap:
    origin_x: int
    origin_y: int
    width: int
    height: int
    layers: List[Layer]
    texture_infos: List[TexturePageInfo]
    sprite_infos: List[SpriteTileInfo]

TilemapConstruct = Struct(
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
                    "tile_clut_data" / ByteSwapped(BitStruct(
                        Padding(6),
                        "clut_number" / BitsInteger(4),
                        Padding(6)
                    ))
                )
            )
        )
    ),
    "texture_page_data" / FixedSized(
        lambda ctx: ctx.sprite_info_offset - ctx.texture_page_offset,
        GreedyRange(
            ByteSwapped(BitStruct(
                Padding(7),
                "depth" / BitsInteger(2),
                "blending_mode" / BitsInteger(2),
                "page_y" / BitsInteger(1),
                "page_x" / BitsInteger(4)
            ))
        )
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
                    "tile_clut_data" / ByteSwapped(BitStruct(
                        Padding(6),
                        "clut_number" / BitsInteger(4),
                        Padding(6)
                    )),
                    "sprite_tp_blend" / ByteSwapped(BitStruct(
                        Padding(7),
                        "depth" / BitsInteger(2),
                        "blending_mode" / BitsInteger(2),
                        "page_y" / BitsInteger(1),
                        "page_x" / BitsInteger(4)
                    )),
                    "group" / Int16ul,
                    "parameter" / Int8ul,
                    "state" / Int8ul
                )
            )
        )
    )
)
