# BDF2UFO
# Converts a .bdf pixel font to a .ufo variable vector font
#
# (C) 2024-2025 Gissio
#
# License: MIT
#

import argparse
from datetime import datetime
import math
import os
import random
import shutil
import sys

import bdflib.reader
import fontTools.designspaceLib
import fontTools.feaLib.builder
import fontTools.feaLib.ast
import fontTools.misc.transform
import fontTools.ufoLib
import fontTools.misc
import numpy as np
import unicodedata
import ufoLib2
import ufoLib2.objects
import ufoLib2.objects.anchor


# Definitions

log_level = 1
bdf2ufo_version = '1.0.1'

weight_from_weight_name = {
    'thin': 100,
    'extralight': 200,
    'ultralight': 200,
    'light': 300,
    'normal': 400,
    'regular': 400,
    'medium': 500,
    'demibold': 600,
    'semibold': 600,
    'bold': 700,
    'extrabold': 800,
    'ultrabold': 800,
    'black': 900,
    'heavy': 900,
}

weight_name_from_weight = {
    100: 'Thin',
    200: 'ExtraLight',
    300: 'Light',
    400: 'Regular',
    500: 'Medium',
    600: 'SemiBold',
    700: 'Bold',
    800: 'ExtraBold',
    900: 'Black',
}

slope_from_slant = {
    'R': '',
    'I': 'Italic',
    'RI': 'Italic',
    'O': 'Oblique',
    'RO': 'Oblique',
}

width_class_from_setwidth_name = {
    'ultracondensed': 1,
    'extracondensed': 2,
    'condensed': 3,
    'semicondensed': 4,
    'normal': 5,
    'semiexpanded': 6,
    'expanded': 7,
    'extraexpanded': 8,
    'ultraexpanded': 9,
}

width_name_from_width_class = {
    1: 'UltraCondensed',
    2: 'ExtraCondensed',
    3: 'Condensed',
    4: 'SemiCondensed',
    5: 'Normal',
    6: 'SemiExpanded',
    7: 'Expanded',
    8: 'ExtraExpanded',
    9: 'UltraExpanded',
}

combining_infos = {
    0x300: ('grave accent', 'top', 0x2cb),
    0x301: ('acute accent', 'top.shifted', 0x2ca),
    0x302: ('circumflex accent', 'top', 0x2c6),
    0x303: ('tilde', 'top.shifted', 0x2dc),
    0x304: ('macron', 'top', 0x2c9),
    0x306: ('breve', 'top', 0x2d8),
    0x307: ('dot above', 'top', 0x2d9),
    0x308: ('diaeresis', 'top', 0xa8),
    0x309: ('hook above', 'top', None),
    0x30a: ('ring above', 'top', 0x2da),
    0x30b: ('double acute accent', 'top.shifted', 0x2dd),
    0x30c: ('caron', 'top', 0x2c7),
    0x30d: ('vertical line above', 'top', 0x2c8),
    0x30f: ('double grave accent', 'top', 0x2f5),
    0x311: ('inverted breve', 'top', 0x1aff),
    0x313: ('comma above', 'top', 0x2c),
    0x314: ('reversed comma above', 'top', None),
    0x315: ('comma above right', 'top.right', 0x2c),
    0x31b: ('horn', 'horn', None),
    0x323: ('dot below', 'bottom', 0x2d9),
    0x324: ('diaeresis below', 'bottom', 0xa8),
    0x325: ('ring below', 'bottom', 0x2da),
    0x326: ('comma below', 'bottom', 0x2c),
    0x327: ('cedilla', 'cedilla', 0xb8),
    0x328: ('ogonek', 'ogonek', 0x2db),
    0x32d: ('circumflex accent below', 'bottom', 0x2c6),
    0x32e: ('breve below', 'bottom', 0x2d8),
    0x32f: ('inverted breve below', 'bottom', 0x1aff),
    0x330: ('tilde below', 'bottom.shifted', 0x2dc),
    0x331: ('macron below', 'bottom', 0x2c9),
    0x332: ('low line', 'top', 0x5f),
    0x335: ('short stroke overlay', 'overlay', None),
    0x342: ('greek perispomeni', 'top.shifted', 0x2dc),
    0x343: ('greek koronis', 'top', 0x2c),
    0x344: ('greek dialytika tonos', 'top', 0xa8),
    0x345: ('greek ypogegrammeni', 'bottom', 0x37a),
    0x359: ('asterisk below', 'bottom', None),
    0x35c: ('double breve below', 'bottom', None),
    0x35f: ('double macron below', 'bottom', 0x2ed),
    0x1dc4: ('macron acute', 'top', None),
    0x1dc5: ('grave macron', 'top', None),
    0x1dc6: ('macron grave', 'top', None),
    0x1dc7: ('acute macron', 'top', None),
    0x1dca: ('latin small letter r below', 'bottom', None),
}

custom_decomposition = {
    0x69: '0131 0307',
    0x6a: '0237 0307',
    0xec: '0131 0300',
    0xed: '0131 0301',
    0xee: '0131 0302',
    0xef: '0131 0308',
    0x10f: '0064 02bc',
    0x122: '0047 0326',
    0x123: '0067 02bb',
    0x129: '0131 0303',
    0x12b: '0131 0304',
    0x12d: '0131 0306',
    0x135: '0237 0302',
    0x136: '004B 0326',
    0x137: '006B 0326',
    0x13b: '004C 0326',
    0x13c: '006C 0326',
    0x13d: '004C 02bc',
    0x13e: '006C 02bc',
    0x145: '004E 0326',
    0x146: '006E 0326',
    0x156: '0052 0326',
    0x157: '0072 0326',
    0x165: '0074 02bc',
    0x17f: '',
    0x1d0: '0131 030c',
    0x1f0: '0237 030c',
    0x209: '0131 030f',
    0x20b: '0131 0311',
    0x385: '0308 0301',
    0x457: '0131 0308',
    0x1ec9: '0131 0309',
    0x1e06: '0042 0331',
    0x1e07: '0062 0331',
    0x1e0e: '0044 0331',
    0x1e0f: '0064 0331',
    0x1e34: '004b 0331',
    0x1e35: '006b 0331',
    0x1e3a: '004c 0331',
    0x1e3b: '006c 0331',
    0x1e48: '004e 0331',
    0x1e49: '006e 0331',
    0x1e5e: '0052 0331',
    0x1e5f: '0072 0331',
    0x1e6e: '0054 0331',
    0x1e6f: '0074 0331',
    0x1e94: '005a 0331',
    0x1e95: '007a 0331',
    0x1f00: '03b1 1fbf',
    0x1f01: '03b1 1ffe',
    0x1f02: '03b1 1fcd',
    0x1f03: '03b1 1fdd',
    0x1f04: '03b1 1fce',
    0x1f05: '03b1 1fde',
    0x1f08: '0391 1fbf',
    0x1f09: '0391 1ffe',
    0x1f0a: '0391 1fcd',
    0x1f0b: '0391 1fdd',
    0x1f0c: '0391 1fce',
    0x1f0d: '0391 1fde',
    0x1f10: '03b5 1fbf',
    0x1f11: '03b5 1ffe',
    0x1f12: '03b5 1fcd',
    0x1f13: '03b5 1fdd',
    0x1f14: '03b5 1fce',
    0x1f15: '03b5 1fde',
    0x1f18: '0395 1fbf',
    0x1f19: '0395 1ffe',
    0x1f1a: '0395 1fcd',
    0x1f1b: '0395 1fdd',
    0x1f1c: '0395 1fce',
    0x1f1d: '0395 1fde',
    0x1f20: '03b7 1fbf',
    0x1f21: '03b7 1ffe',
    0x1f22: '03b7 1fcd',
    0x1f23: '03b7 1fdd',
    0x1f24: '03b7 1fce',
    0x1f25: '03b7 1fde',
    0x1f28: '0397 1fbf',
    0x1f29: '0397 1ffe',
    0x1f2a: '0397 1fcd',
    0x1f2b: '0397 1fdd',
    0x1f2c: '0397 1fce',
    0x1f2d: '0397 1fde',
    0x1f30: '03b9 1fbf',
    0x1f31: '03b9 1ffe',
    0x1f32: '03b9 1fcd',
    0x1f33: '03b9 1fdd',
    0x1f34: '03b9 1fce',
    0x1f35: '03b9 1fde',
    0x1f38: '0399 1fbf',
    0x1f39: '0399 1ffe',
    0x1f3a: '0399 1fcd',
    0x1f3b: '0399 1fdd',
    0x1f3c: '0399 1fce',
    0x1f3d: '0399 1fde',
    0x1f40: '03bf 1fbf',
    0x1f41: '03bf 1ffe',
    0x1f42: '03bf 1fcd',
    0x1f43: '03bf 1fdd',
    0x1f44: '03bf 1fce',
    0x1f45: '03bf 1fde',
    0x1f48: '039f 1fbf',
    0x1f49: '039f 1ffe',
    0x1f4a: '039f 1fcd',
    0x1f4b: '039f 1fdd',
    0x1f4c: '039f 1fce',
    0x1f4d: '039f 1fde',
    0x1f50: '03c5 1fbf',
    0x1f51: '03c5 1ffe',
    0x1f52: '03c5 1fcd',
    0x1f53: '03c5 1fdd',
    0x1f54: '03c5 1fce',
    0x1f55: '03c5 1fde',
    0x1f59: '03a5 1ffe',
    0x1f5b: '03a5 1fdd',
    0x1f5d: '03a5 1fde',
    0x1f60: '03c9 1fbf',
    0x1f61: '03c9 1ffe',
    0x1f62: '03c9 1fcd',
    0x1f63: '03c9 1fdd',
    0x1f64: '03c9 1fce',
    0x1f65: '03c9 1fde',
    0x1f68: '03a9 1fbf',
    0x1f69: '03a9 1ffe',
    0x1f6a: '03a9 1fcd',
    0x1f6b: '03a9 1fdd',
    0x1f6c: '03a9 1fce',
    0x1f6d: '03a9 1fde',
    0x1fbd: '',
    0x1fbe: '037a',
    0x1fbf: '',
    0x1fc1: '0308 0342',
    0x1fe4: '03c1 1fbf',
    0x1fe5: '03c1 1ffe',
    0x1fed: '0308 0300',
    0x1fee: '0308 0301',
    0x1ff9: '039f 0301',
    0x2116: '004e 00ba',
}

custom_anchors = [
    0x3b6, 0x3b8, 0x3b9, 0x3ba, 0x3bc, 0x3be, 0x3bf,
    0x1f02, 0x1f03, 0x1f04, 0x1f05, 0x1f08, 0x1f09, 0x1f0a, 0x1f0b, 0x1f0c, 0x1f0d,
    0x1f12, 0x1f13, 0x1f14, 0x1f15, 0x1f18, 0x1f19, 0x1f1a, 0x1f1b, 0x1f1c, 0x1f1d,
    0x1f22, 0x1f23, 0x1f24, 0x1f25, 0x1f28, 0x1f29, 0x1f2a, 0x1f2b, 0x1f2c, 0x1f2d,
    0x1f32, 0x1f33, 0x1f34, 0x1f35, 0x1f38, 0x1f39, 0x1f3a, 0x1f3b, 0x1f3c, 0x1f3d,
    0x1f42, 0x1f43, 0x1f44, 0x1f45, 0x1f48, 0x1f49, 0x1f4a, 0x1f4b, 0x1f4c, 0x1f4d,
    0x1f52, 0x1f53, 0x1f54, 0x1f55, 0x1f59, 0x1f5b, 0x1f5c,
    0x1f62, 0x1f63, 0x1f64, 0x1f65, 0x1f68, 0x1f69, 0x1f6a, 0x1f6b, 0x1f6c, 0x1f6d,
    0x1f82, 0x1f83, 0x1f84, 0x1f85, 0x1f88, 0x1f89, 0x1f8a, 0x1f8b, 0x1f8c, 0x1f8d,
    0x1f92, 0x1f93, 0x1f94, 0x1f95, 0x1f98, 0x1f99, 0x1f9a, 0x1f9b, 0x1f9c, 0x1f9d,
    0x1fa2, 0x1fa3, 0x1fa4, 0x1fa5, 0x1fa8, 0x1fa9, 0x1faa, 0x1fab, 0x1fac, 0x1fad,
    0x1fba, 0x1fbb,
    0x1fc1, 0x1fc8, 0x1fc9, 0x1fca, 0x1fcb, 0x1fcd, 0x1fce, 0x1fcf,
    0x1fda, 0x1fdb, 0x1fdd, 0x1fde, 0x1fdf,
    0x1fea, 0x1feb, 0x1fec, 0x1fed, 0x1fee,
    0x1ff8, 0x1ff9, 0x1ffa, 0x1ffb
]

# ID: Label, min, max, default
axes_info = {
    'ESIZ': {'name': 'Element Size', 'min': 0.1, 'max': 1, 'default': 1},
    'ROND': {'name': 'Roundness', 'min': 0, 'max': 1, 'default': 0},
    'BLED': {'name': 'Bleed', 'min': 0, 'max': 1, 'default': 0},
    'XESP': {'name': 'Horizontal Element Spacing', 'min': 0.5, 'max': 1, 'default': 1},
    'EJIT': {'name': 'Element Jitter', 'min': 0, 'max': 0.1, 'default': 0},
}


class Object(object):
    pass


def auto_int(x):
    return int(x, 0)


def log_info(message):
    if log_level <= 0:
        print("info: " + message)


def log_warning(message):
    if log_level <= 1:
        print("warning: " + message)


def log_error(message):
    if log_level <= 2:
        print("error: " + message)

    sys.exit(1)


def get_unicode_string(codepoint):
    return 'U+' + f'{codepoint:04x}'


def get_decomposition_string(decomposition):
    return ', '.join([get_unicode_string(codepoint) for codepoint in decomposition])


def match_codepoint(codepoint_range, codepoint):
    if codepoint_range == '':
        return True

    for token in codepoint_range.split(','):
        element = token.split('-', 1)
        if len(element) == 1:
            if codepoint == int(element[0], 0):
                return True
        else:
            if codepoint >= int(element[0], 0) and\
                    codepoint <= int(element[1], 0):
                return True

    return False


def get_bdf_property(bdf, key, default_value):
    key = key.encode('utf-8')

    if key in bdf.properties:
        value = bdf.properties[key]
        if isinstance(value, int):
            return value

        else:
            return value.decode('utf-8')

    else:
        return default_value


def filter_name(name):
    return ''.join([c for c in name.lower() if c.isalpha()])


def set_bdf_property(bdf_font, config, key, default_value):
    value = getattr(config, key)

    if value is not None:
        setattr(bdf_font, key, value)

    else:
        setattr(bdf_font, key, default_value)


def parse_axes_string(axes_string):
    axes = {}

    if axes_string == None:
        return axes

    for axis_string in axes_string.split(','):
        if axis_string == '':
            continue

        axis_components = axis_string.split('=', 2)
        axis = axis_components[0]

        if axis not in axes_info:
            log_error(
                f'invalid axis {axis} in parameter: {axes_string}')

        if len(axis_components) == 1:
            axes[axis] = 0
        elif len(axis_components) == 2:
            axes[axis] = float(axis_components[1])

    return axes


def load_bdf(config):
    bdf_boundingbox0 = [sys.maxsize, sys.maxsize]
    bdf_boundingbox1 = [-sys.maxsize, -sys.maxsize]

    bdf_font = Object()

    with open(config.input, "rb") as handle:
        bdf = bdflib.reader.read_bdf(handle)

        bdf_font.glyphs = {}
        bdf_font.codepoints = {}

        cap_height = bdf.ptSize
        x_height = bdf.ptSize

        # Set font glyphs
        for bdf_glyph in bdf.glyphs:
            codepoint = bdf_glyph.codepoint

            name = bdf_glyph.name.decode('utf-8')

            if codepoint == config.notdef_codepoint:
                name = '.notdef'

            else:
                if not match_codepoint(config.codepoint_subset, codepoint):
                    continue

                # Sanitize glyph name
                if not name[0].isalnum():
                    name = '_' + name

                name = ''.join(
                    [c if (c.isalnum() or c == '.') else '_' for c in name])

                while name in bdf_font.glyphs:
                    name += '_'

            # Build bitmap
            bitmap = np.zeros((bdf_glyph.bbH, bdf_glyph.bbW), np.uint8)
            for y in range(bdf_glyph.bbH):
                value = bdf_glyph.data[y]
                for x in range(bdf_glyph.bbW):
                    bitmap[y][x] = (value >> (bdf_glyph.bbW - x - 1)) & 1

            # Crop bitmap
            if bitmap.any():
                bitmap_coords = np.argwhere(bitmap)
                y_min, x_min = bitmap_coords.min(axis=0)
                y_max, x_max = bitmap_coords.max(axis=0)
                y_max += 1
                x_max += 1

            else:
                y_min, x_min = 0, 0
                y_max, x_max = 1, 1

            bitmap = bitmap[y_min:y_max,
                            x_min:x_max]

            # Update font bounding box
            boundingbox0 = (bdf_glyph.bbY + int(y_min),
                            bdf_glyph.bbX + int(x_min))
            boundingbox1 = (boundingbox0[0] + bitmap.shape[0],
                            boundingbox0[1] + bitmap.shape[1])

            bdf_boundingbox0[0] = min(bdf_boundingbox0[0], boundingbox0[0])
            bdf_boundingbox0[1] = min(bdf_boundingbox0[1], boundingbox0[1])
            bdf_boundingbox1[0] = max(bdf_boundingbox1[0], boundingbox1[0])
            bdf_boundingbox1[1] = max(bdf_boundingbox1[1], boundingbox1[1])

            advance = bdf_glyph.advance

            # Build glyph
            bdf_glyph = Object()
            bdf_glyph.codepoint = codepoint
            bdf_glyph.bitmap = bitmap
            bdf_glyph.offset = boundingbox0
            bdf_glyph.advance = advance

            if codepoint == 0x41:
                cap_height = bitmap.shape[0]
            elif codepoint == 0x78:
                x_height = bitmap.shape[0]

            bdf_font.glyphs[name] = bdf_glyph
            bdf_font.codepoints[codepoint] = name

        # Add undefined combining glyphs
        for combining_codepoint in combining_infos:
            _, _, modifier_codepoint = combining_infos[combining_codepoint]

            if modifier_codepoint in bdf_font.codepoints and\
                    combining_codepoint not in bdf_font.codepoints and\
            match_codepoint(config.codepoint_subset, combining_codepoint):
                modifier_name = bdf_font.codepoints[modifier_codepoint]
                modifier_glyph = bdf_font.glyphs[modifier_name]

                combining_name = f'uni{combining_codepoint:04x}'

                combining_glyph = Object()
                combining_glyph.codepoint = combining_codepoint
                combining_glyph.bitmap = modifier_glyph.bitmap
                combining_glyph.offset = modifier_glyph.offset
                combining_glyph.advance = modifier_glyph.advance

                bdf_font.glyphs[combining_name] = combining_glyph
                bdf_font.codepoints[combining_codepoint] = combining_name

        # Set font info
        set_bdf_property(bdf_font, config, 'font_version',
                         get_bdf_property(bdf, 'FONT_VERSION', ''))
        set_bdf_property(bdf_font, config, 'family_name',
                         get_bdf_property(bdf, 'FAMILY_NAME', bdf.name.decode('utf-8')))
        weight_name = filter_name(get_bdf_property(bdf, 'WEIGHT_NAME', ''))
        if weight_name in weight_from_weight_name:
            weight = weight_from_weight_name[weight_name]
        else:
            weight = 400
        set_bdf_property(bdf_font, config, 'weight', weight)
        slant = get_bdf_property(bdf, 'SLANT', '').upper()
        if slant in slope_from_slant:
            slope = slope_from_slant[slant]
        else:
            slope = ''
        set_bdf_property(bdf_font, config, 'slope', slope)
        setwidth_name = filter_name(
            get_bdf_property(bdf, 'SETWIDTH_NAME', ''))
        if setwidth_name in width_class_from_setwidth_name:
            width_class = width_class_from_setwidth_name[setwidth_name]
        else:
            width_class = 5
        set_bdf_property(bdf_font, config, 'width_class', width_class)

        set_bdf_property(bdf_font, config, 'copyright',
                         get_bdf_property(bdf, 'COPYRIGHT',
                                          '\n'.join([s.decode('utf-8')
                                                     for s in bdf.comments])))
        set_bdf_property(bdf_font, config, 'designer', '')
        set_bdf_property(bdf_font, config, 'designer_url', '')
        set_bdf_property(bdf_font, config, 'manufacturer',
                         get_bdf_property(bdf, 'FOUNDRY', ''))
        set_bdf_property(bdf_font, config, 'manufacturer_url', '')
        set_bdf_property(bdf_font, config, 'license', '')
        set_bdf_property(bdf_font, config, 'license_url', '')

        set_bdf_property(bdf_font, config, 'ascent',
                         get_bdf_property(bdf, 'FONT_ASCENT', bdf.ptSize))
        set_bdf_property(bdf_font, config, 'descent',
                         -get_bdf_property(bdf, 'FONT_DESCENT', 0))
        set_bdf_property(bdf_font, config, 'cap_height',
                         get_bdf_property(bdf, 'CAP_HEIGHT', cap_height))
        set_bdf_property(bdf_font, config, 'x_height',
                         get_bdf_property(bdf, 'X_HEIGHT', x_height))

        set_bdf_property(bdf_font, config, 'underline_position',
                         get_bdf_property(bdf, 'UNDERLINE_POSITION', 0))
        set_bdf_property(bdf_font, config, 'underline_thickness',
                         get_bdf_property(bdf, 'UNDERLINE_THICKNESS', 0))
        set_bdf_property(bdf_font, config, 'strikeout_position',
                         get_bdf_property(bdf, 'STRIKEOUT_ASCENT', 0))
        set_bdf_property(bdf_font, config, 'strikeout_thickness',
                         get_bdf_property(bdf, 'STRIKEOUT_DESCENT', 0))

        set_bdf_property(bdf_font, config, 'superscript_size',
                         get_bdf_property(bdf, 'SUPERSCRIPT_SIZE',
                                          int(0.6 * bdf_font.cap_height)))
        set_bdf_property(bdf_font, config, 'superscript_x',
                         get_bdf_property(bdf, 'SUPERSCRIPT_X',
                                          bdf_font.cap_height - bdf_font.superscript_size))
        set_bdf_property(bdf_font, config, 'superscript_y',
                         get_bdf_property(bdf, 'SUPERSCRIPT_Y',
                                          bdf_font.cap_height - bdf_font.superscript_size))
        set_bdf_property(bdf_font, config, 'subscript_size',
                         get_bdf_property(bdf, 'SUBSCRIPT_SIZE',
                                          int(0.6 * bdf_font.cap_height)))
        set_bdf_property(bdf_font, config, 'subscript_x',
                         get_bdf_property(bdf, 'SUBSCRIPT_X',
                                          bdf_font.cap_height - bdf_font.subscript_size))
        set_bdf_property(bdf_font, config, 'subscript_y',
                         get_bdf_property(bdf, 'SUBSCRIPT_Y',
                                          bdf_font.cap_height - bdf_font.subscript_size))

        bdf_font.boundingbox = (bdf_boundingbox0, bdf_boundingbox1)
        bdf_font.glyph_offset_x = config.glyph_offset_x
        bdf_font.glyph_offset_y = config.glyph_offset_y
        bdf_font.units_per_em = config.units_per_em

        bdf_font.variable_axes = [
            key for key in parse_axes_string(config.variable_axes)]

        bdf_font.variable_instances = []
        if len(bdf_font.variable_axes) > 0:
            for instance_string in config.variable_instance:
                variable_instance = Object()

                components = instance_string.split(',')
                variable_instance.name = components[0]
                variable_instance.location = parse_axes_string(
                    ','.join(components[1:]))

                bdf_font.variable_instances.append(variable_instance)

        else:
            variable_instance = Object()
            variable_instance.name = ''
            variable_instance.location = []

            bdf_font.variable_instances.append(variable_instance)

        bdf_font.location = {}
        for axis in axes_info:
            bdf_font.location[axis] = axes_info[axis]['default']
        location = parse_axes_string(config.static_axes)
        for axis in location:
            bdf_font.location[axis] = location[axis]

        bdf_font.units_per_element_y = int(bdf_font.units_per_em /
                                           (bdf_font.ascent - bdf_font.descent))

        bdf_font.custom_style_name = config.custom_style_name

    return bdf_font


def add_offset(a, b):
    return (a[0] + b[0], a[1] + b[1])


def subtract_offset(a, b):
    return (a[0] - b[0], a[1] - b[1])


def get_units_per_element_x(bdf_font):
    return bdf_font.location['XESP'] * bdf_font.units_per_element_y


def get_style_name(bdf_font, instance_name=''):
    style_name = ''

    if bdf_font.custom_style_name != '':
        style_name += bdf_font.custom_style_name + ' '

    if instance_name != '':
        style_name += instance_name + ' '

    if bdf_font.width_class != 5:
        style_name = width_name_from_width_class() + ' '

    style_name += weight_name_from_weight[bdf_font.weight]

    if bdf_font.slope != '':
        style_name += ' ' + bdf_font.slope

    return style_name


def get_file_name(bdf_font, sub_style_name=''):
    return bdf_font.family_name.replace(' ', '') + '-' + sub_style_name +\
        get_style_name(bdf_font).replace(' ', '')


def set_ufo_info(ufo_font, bdf_font):
    # Ascenders and descenders
    line_ascender = bdf_font.ascent * bdf_font.units_per_element_y
    line_descender = bdf_font.descent * bdf_font.units_per_element_y
    line_height = line_ascender - line_descender

    em_descender = line_descender - \
        int((bdf_font.units_per_em - line_height) / 2)
    em_ascender = bdf_font.units_per_em + em_descender

    # Style map style name
    if bdf_font.weight == 700:
        style_map_style_name = 'bold'
    else:
        style_map_style_name = 'regular'

    if bdf_font.slope != '':
        style_map_style_name += ' italic'

    # Version
    version_components = bdf_font.font_version.split(';', 2)
    if version_components[0].startswith('Version '):
        version_components[0] = version_components[8:]
    font_version = 'Version ' + ';'.join(version_components)

    version_number_components = version_components[0].split('.')
    version_majorminor = (1, 0)
    if len(version_number_components) == 2:
        try:
            version_number_components = (
                int(version_number_components[0]),
                int(version_number_components[1]))
        except:
            pass

    # Set info
    ufo_info = ufo_font.info

    ufo_info.familyName = bdf_font.family_name
    ufo_info.styleName = get_style_name(bdf_font)
    ufo_info.versionMajor, ufo_info.versionMinor = version_majorminor

    ufo_info.copyright = bdf_font.copyright
    ufo_info.unitsPerEm = bdf_font.units_per_em
    ufo_info.descender = em_descender
    ufo_info.xHeight = bdf_font.x_height * bdf_font.units_per_element_y
    ufo_info.capHeight = bdf_font.cap_height * bdf_font.units_per_element_y
    ufo_info.ascender = em_ascender

    ufo_info.guidelines = []

    ufo_info.openTypeHheaAscender = line_ascender
    ufo_info.openTypeHheaDescender = line_descender
    ufo_info.openTypeHheaLineGap = 0

    ufo_info.openTypeNameDesigner = bdf_font.designer
    ufo_info.openTypeNameDesignerURL = bdf_font.designer_url
    ufo_info.openTypeNameManufacturer = bdf_font.manufacturer
    ufo_info.openTypeNameManufacturerURL = bdf_font.manufacturer_url
    ufo_info.openTypeNameLicense = bdf_font.license
    ufo_info.openTypeNameLicenseURL = bdf_font.license_url
    ufo_info.openTypeNameVersion = font_version

    ufo_info.openTypeOS2WidthClass = bdf_font.width_class
    ufo_info.openTypeOS2WeightClass = bdf_font.weight
    ufo_info.openTypeOS2VendorID = "B2UF"
    ufo_info.openTypeOS2TypoAscender = ufo_info.openTypeHheaAscender
    ufo_info.openTypeOS2TypoDescender = ufo_info.openTypeHheaDescender
    ufo_info.openTypeOS2TypoLineGap = ufo_info.openTypeHheaLineGap
    ufo_info.openTypeOS2WinAscent = max(
        bdf_font.boundingbox[1][0] * bdf_font.units_per_element_y, 0)
    ufo_info.openTypeOS2WinDescent = max(
        -bdf_font.boundingbox[0][0] * bdf_font.units_per_element_y, 0)
    ufo_info.openTypeOS2SubscriptXSize = bdf_font.subscript_size * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2SubscriptYSize = bdf_font.subscript_size * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2SubscriptXOffset = bdf_font.subscript_x * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2SubscriptYOffset = bdf_font.subscript_y * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2SuperscriptXSize = bdf_font.superscript_size * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2SuperscriptYSize = bdf_font.superscript_size * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2SuperscriptXOffset = bdf_font.superscript_x * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2SuperscriptYOffset = bdf_font.superscript_y * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2StrikeoutSize = bdf_font.strikeout_thickness * \
        bdf_font.units_per_element_y
    ufo_info.openTypeOS2StrikeoutPosition = bdf_font.strikeout_position * \
        bdf_font.units_per_element_y

    ufo_info.postscriptUnderlineThickness = bdf_font.underline_thickness * \
        bdf_font.units_per_element_y
    ufo_info.postscriptUnderlinePosition = bdf_font.underline_position * \
        bdf_font.units_per_element_y


def add_element_glyph(ufo_font, bdf_font):
    units_per_pixel = bdf_font.location['ESIZ'] * bdf_font.units_per_element_y
    unit = units_per_pixel / 2
    radius = bdf_font.location['ROND'] * unit

    # # Cubic curves
    tangent = radius * (4 / 3) * math.tan(math.radians(90 / 4))
    max_x = unit + bdf_font.location['BLED'] * (units_per_pixel - unit)
    max_y = unit
    min_x = max_x - radius
    min_y = max_y - radius
    tangent_x = min_x + tangent
    tangent_y = min_y + tangent

    element_points = [
        [(min_y, max_x), 'curve'],
        [(-min_y, max_x), 'line'],
        [(-tangent_y, max_x), 'offcurve'],
        [(-max_y, tangent_x), 'offcurve'],
        [(-max_y, min_x), 'curve'],
        [(-max_y, -min_x), 'line'],
        [(-max_y, -tangent_x), 'offcurve'],
        [(-tangent_y, -max_x), 'offcurve'],
        [(-min_y, -max_x), 'curve'],
        [(min_y, -max_x), 'line'],
        [(tangent_y, -max_x), 'offcurve'],
        [(max_y, -tangent_x), 'offcurve'],
        [(max_y, -min_x), 'curve'],
        [(max_y, min_x), 'line'],
        [(max_y, tangent_x), 'offcurve'],
        [(tangent_y, max_x), 'offcurve'],
    ]

    # Quadratic curve
    # midarc = radius * math.cos(math.radians(45))
    # tangent = radius * (4 / 3) * math.tan(math.radians(90 / 4))
    # max_x = unit + bdf_font.location['BLED'] * (2 * units_per_pixel - unit)
    # max_y = unit
    # min_x = max_x - radius
    # min_y = max_y - radius
    # tangent_x = min_x + tangent
    # tangent_y = min_y + tangent
    # midarc_x = min_x + midarc
    # midarc_y = min_y + midarc

    # element_points = [
    #     [(min_y, max_x), 'qcurve'],
    #     [(-min_y, max_x), 'line'],
    #     [(-tangent_y, max_x), 'offcurve'],
    #     [(-midarc_y, midarc_x), 'qcurve'],
    #     [(-max_y, tangent_x), 'offcurve'],
    #     [(-max_y, min_x), 'qcurve'],
    #     [(-max_y, -min_x), 'line'],
    #     [(-max_y, -tangent_x), 'offcurve'],
    #     [(-midarc_y, -midarc_x), 'qcurve'],
    #     [(-tangent_y, -max_x), 'offcurve'],
    #     [(-min_y, -max_x), 'qcurve'],
    #     [(min_y, -max_x), 'line'],
    #     [(tangent_y, -max_x), 'offcurve'],
    #     [(midarc_y, -midarc_x), 'qcurve'],
    #     [(max_y, -tangent_x), 'offcurve'],
    #     [(max_y, -min_x), 'qcurve'],
    #     [(max_y, min_x), 'line'],
    #     [(max_y, tangent_x), 'offcurve'],
    #     [(midarc_y, midarc_x), 'qcurve'],
    #     [(tangent_y, max_x), 'offcurve'],
    # ]

    ufo_points = []
    for point_offset, point_type in element_points:
        ufo_points.append(
            ufoLib2.objects.Point(
                point_offset[1],
                point_offset[0],
                point_type)
        )

    ufo_contour = ufoLib2.objects.Contour(ufo_points)

    ufo_glyph = ufo_font.newGlyph('_')
    ufo_glyph.appendContour(ufo_contour)


def paint_bdf_glyph(composed_bitmap,
                    component_bitmap,
                    offset,
                    bitmap):
    for y in range(component_bitmap.shape[0]):
        for x in range(component_bitmap.shape[1]):
            if component_bitmap[y][x]:
                bitmap_y = offset[0] + y
                bitmap_x = offset[1] + x

                if not composed_bitmap[bitmap_y][bitmap_x]:
                    return False

                bitmap[bitmap_y][bitmap_x] = 1

    return True


def get_bdf_components(bdf_font,
                       composed_glyph,
                       decomposition,
                       bitmap):
    if not isinstance(bitmap, np.ndarray):
        bitmap = np.zeros(composed_glyph.bitmap.shape, np.uint8)

    if len(decomposition) == 0:
        if (composed_glyph.bitmap == bitmap).all():
            return []

        return 'mismatch'

    component_codepoint = decomposition[0]

    for stage in range(2):
        if stage == 0:
            if component_codepoint not in bdf_font.codepoints:
                continue

        else:
            if component_codepoint not in combining_infos:
                break

            _, _, modifier_codepoint = combining_infos[component_codepoint]

            if modifier_codepoint == composed_glyph.codepoint:
                return 'uncomposable'

            if modifier_codepoint not in bdf_font.codepoints:
                return 'missing'

            component_codepoint = modifier_codepoint

        component_name = bdf_font.codepoints[component_codepoint]
        component_glyph = bdf_font.glyphs[component_name]

        delta_size = subtract_offset(
            composed_glyph.bitmap.shape, component_glyph.bitmap.shape)

        for offset_y in range(delta_size[0] + 1):
            for offset_x in range(delta_size[1] + 1):
                offset = (offset_y, offset_x)
                bitmap_copy = bitmap.copy()

                if not paint_bdf_glyph(composed_glyph.bitmap,
                                       component_glyph.bitmap,
                                       offset,
                                       bitmap_copy):
                    continue

                bdf_components = get_bdf_components(bdf_font,
                                                    composed_glyph,
                                                    decomposition[1:],
                                                    bitmap_copy)

                if bdf_components in ['missing', 'uncomposable']:
                    return bdf_components

                elif isinstance(bdf_components, list):
                    bdf_component = Object()
                    bdf_component.name = component_name
                    bdf_component.offset = add_offset(
                        composed_glyph.offset, offset)
                    bdf_components.append(bdf_component)

                    return bdf_components

    if component_codepoint not in bdf_font.codepoints:
        return 'missing'

    else:
        return 'mismatch'


def decompose_bdf_glyph(bdf_font, composed_name):
    composed_glyph = bdf_font.glyphs[composed_name]
    composed_codepoint = composed_glyph.codepoint

    # Calculate decomposition
    if composed_codepoint in custom_decomposition:
        decomposition_string = custom_decomposition[composed_codepoint]
    elif composed_codepoint >= 0:
        decomposition_string = unicodedata.decomposition(
            chr(composed_codepoint))
    else:
        decomposition_string = ''

    if decomposition_string.startswith('<compat> '):
        decomposition_string = decomposition_string[9:]
    if decomposition_string == '' or decomposition_string.startswith('<'):
        return []
    decomposition = [int(x, 16) for x in decomposition_string.split()]

    decomposition = [x for x in decomposition if x != 0x20]

    # Get components
    components = get_bdf_components(bdf_font,
                                    composed_glyph,
                                    decomposition,
                                    None)

    if components == 'missing':
        log_info(f'{get_unicode_string(composed_codepoint)}'
                 ' could be composed from ['
                 f'{get_decomposition_string(decomposition)}]')

        return []

    elif components == 'mismatch':
        log_warning(f'{get_unicode_string(composed_codepoint)}'
                    ' cannot be composed from ['
                    f'{get_decomposition_string(decomposition)}]'
                    ', storing precomposed glyph')

        return []

    elif components == 'uncomposable':
        return []

    else:
        log_info(f'{get_unicode_string(composed_codepoint)}'
                 ' composed with [' +
                 f'{get_decomposition_string(decomposition)}]')

        return components


def get_random_offset(bdf_font):
    while True:
        value = random.gauss(0, bdf_font.location['EJIT'])

        if math.fabs(value) < 1:
            break

    return value * bdf_font.units_per_element_y


def add_ufo_bitmap(ufo_glyph,
                   bdf_font,
                   bdf_glyph):
    units_per_element_x = get_units_per_element_x(bdf_font)

    for y in range(bdf_glyph.bitmap.shape[0]):
        for x in range(bdf_glyph.bitmap.shape[1]):
            if bdf_glyph.bitmap[y][x]:
                ufo_y = (bdf_glyph.offset[0] + y + 0.5) * \
                    bdf_font.units_per_element_y + get_random_offset(bdf_font)
                ufo_x = (bdf_font.glyph_offset_x +
                         bdf_glyph.offset[1] + x + 0.5) * \
                    units_per_element_x + get_random_offset(bdf_font)

                ufo_component = ufoLib2.objects.Component('_')
                ufo_component.transformation = [
                    1, 0, 0, 1,
                    math.floor(ufo_x),
                    math.floor(ufo_y)]

                ufo_glyph.components.append(ufo_component)


def add_ufo_components(ufo_glyph,
                       bdf_font,
                       components):
    units_per_element_x = get_units_per_element_x(bdf_font)

    for component in components:
        ufo_component = ufoLib2.objects.Component(component.name)

        delta = subtract_offset(component.offset,
                                bdf_font.glyphs[component.name].offset)

        if delta != (0, 0):
            ufo_component.transformation = [
                1, 0, 0, 1,
                math.floor(delta[1] * units_per_element_x),
                math.floor(delta[0] * bdf_font.units_per_element_y)]

        ufo_glyph.components.append(ufo_component)


def add_anchors(anchors,
                bdf_font,
                composed_codepoint,
                components):
    if composed_codepoint in custom_anchors:
        return

    if len(components) != 2:
        return

    # Get base and combining glyphs
    base_name = None
    combining_name = None

    for component in components:
        component_name = component.name
        component_glyph = bdf_font.glyphs[component_name]
        component_codepoint = component_glyph.codepoint

        if component_codepoint in combining_infos:
            combining_name = component_name
            combining_size = component_glyph.bitmap.shape
            combining_glyph_offset = component_glyph.offset
            combining_offset = component.offset

            combining_info = combining_infos[component_codepoint]
            anchor_name = combining_info[1]

        else:
            base_name = component_name
            base_glyph_offset = component_glyph.offset
            base_offset = component.offset

    if base_name == None or combining_name == None:
        return

    # Process combining component
    if combining_name not in anchors:
        anchors[combining_name] = {}

    combining_anchors = anchors[combining_name]
    if anchor_name not in combining_anchors:
        if anchor_name not in ['bottom', 'cedilla', 'ogonek']:
            combining_anchor_offset = (0,
                                       int(combining_size[1] / 2))
        else:
            combining_anchor_offset = (combining_size[0],
                                       int(combining_size[1] / 2))

        combining_anchors[anchor_name] = add_offset(combining_glyph_offset,
                                                    combining_anchor_offset)

    else:
        combining_anchor_offset = subtract_offset(combining_anchors[anchor_name],
                                                  combining_glyph_offset)

    anchor_offset = add_offset(combining_offset,
                               combining_anchor_offset)

    # Process base component
    base_name = base_name

    if base_name not in anchors:
        anchors[base_name] = {}

    anchor_offset = add_offset(
        subtract_offset(anchor_offset,
                        base_offset),
        base_glyph_offset)

    base_anchors = anchors[base_name]
    if anchor_name not in base_anchors:
        base_anchors[anchor_name] = anchor_offset
    else:
        if base_anchors[anchor_name] != anchor_offset:
            log_warning(
                f'{get_unicode_string(composed_codepoint)} anchor "{
                    anchor_name}"'
                ' does not align with anchors from components [' +
                ', '.join([component.name for component in components]) + ']'
            )


def set_ufo_anchors(ufo_font, bdf_font, anchors):
    units_per_element_x = get_units_per_element_x(bdf_font)

    # UFO anchors, base and mark lists
    mark_map = {}
    base_map = {}

    for component_name in anchors:
        component_codepoint = bdf_font.glyphs[component_name].codepoint

        component_anchors = anchors[component_name]
        ufo_glyph = ufo_font[component_name]

        for anchor_name in component_anchors:
            anchor_offset = component_anchors[anchor_name]

            anchor = ufoLib2.objects.Anchor(
                math.floor(
                    (anchor_offset[1] + bdf_font.glyph_offset_x) * units_per_element_x),
                math.floor(
                    anchor_offset[0] * bdf_font.units_per_element_y),
                anchor_name)

            ufo_glyph.appendAnchor(anchor)

            if component_codepoint in combining_infos:
                anchor_name_offset = (anchor_name, anchor_offset)

                if anchor_name_offset not in mark_map:
                    mark_map[anchor_name_offset] = []

                mark_map[anchor_name_offset].append(component_name)

        if component_codepoint not in combining_infos:
            anchor_names_offsets = tuple(
                [(anchor_name, anchor_offset)
                 for anchor_name, anchor_offset
                 in component_anchors.items()])

            if anchor_names_offsets not in base_map:
                base_map[anchor_names_offsets] = []

            base_map[anchor_names_offsets].append(component_name)

    # OpenType features
    features = fontTools.feaLib.builder.FeatureFile()

    # Language systems
    features.statements.append(
        fontTools.feaLib.ast.LanguageSystemStatement('DFLT', 'dflt'))
    if 0x41 in bdf_font.codepoints:
        features.statements.append(
            fontTools.feaLib.ast.LanguageSystemStatement('latn', 'dflt'))
    if 0x391 in bdf_font.codepoints:
        features.statements.append(
            fontTools.feaLib.ast.LanguageSystemStatement('grek', 'dflt'))
    if 0x410 in bdf_font.codepoints:
        features.statements.append(
            fontTools.feaLib.ast.LanguageSystemStatement('cyrl', 'dflt'))

    # Mark definitions
    allmarks = fontTools.feaLib.ast.GlyphClass()
    topmarks = fontTools.feaLib.ast.GlyphClass()

    for codepoint in combining_infos:
        if codepoint in bdf_font.codepoints:
            allmarks.append(bdf_font.codepoints[codepoint])

            if combining_infos[codepoint][1] in ['top', 'top.shifted']:
                topmarks.append(bdf_font.codepoints[codepoint])

    allmarks_definition = fontTools.feaLib.ast.GlyphClassDefinition(
        'allmarks', allmarks)
    features.statements.append(allmarks_definition)

    topmarks_definition = fontTools.feaLib.ast.GlyphClassDefinition(
        'topmarks', topmarks)
    features.statements.append(topmarks_definition)

    # Mark feature
    if len(mark_map) > 0 and len(base_map) > 0:
        mark_lookup = fontTools.feaLib.ast.LookupBlock('marklookup')

        for anchor_name_offset in mark_map:
            anchor_name, anchor_offset = anchor_name_offset
            component_names = mark_map[anchor_name_offset]

            glyphs = fontTools.feaLib.ast.GlyphClass()
            for component_name in component_names:
                glyphs.append(fontTools.feaLib.ast.GlyphName(component_name))

            mark_class = fontTools.feaLib.ast.MarkClassDefinition(
                fontTools.feaLib.ast.MarkClass(anchor_name),
                fontTools.feaLib.ast.Anchor(
                    int(anchor_offset[1] * units_per_element_x),
                    int(anchor_offset[0] * bdf_font.units_per_element_y)),
                glyphs
            )
            mark_lookup.statements.append(mark_class)

        for anchor_name_offsets, component_names in base_map.items():
            glyphs = fontTools.feaLib.ast.GlyphClass()
            for component_name in component_names:
                glyphs.append(fontTools.feaLib.ast.GlyphName(component_name))

            marks = []
            for anchor_name_offset in anchor_name_offsets:
                anchor_name, anchor_offset = anchor_name_offset
                marks.append((
                    fontTools.feaLib.ast.Anchor(
                        int(anchor_offset[1] * units_per_element_x),
                        int(anchor_offset[0] * bdf_font.units_per_element_y)),
                    fontTools.feaLib.ast.MarkClass(anchor_name)
                ))

            base_class = fontTools.feaLib.ast.MarkBasePosStatement(
                glyphs,
                marks)
            mark_lookup.statements.append(base_class)

        features.statements.append(mark_lookup)

        mark_block = fontTools.feaLib.ast.FeatureBlock('mark')
        mark_block.statements.append(
            fontTools.feaLib.ast.LookupReferenceStatement(mark_lookup))

        features.statements.append(mark_block)

    # GDEF table
    allmarks_name = fontTools.feaLib.ast.GlyphClassName(allmarks_definition)

    gdef_table = fontTools.feaLib.ast.TableBlock('GDEF')
    gdef_table.statements.append(
        fontTools.feaLib.ast.GlyphClassDefStatement(
            None, allmarks_name, None,  None))

    features.statements.append(gdef_table)

    # Assign to UFO font
    ufo_font.features.text = features.asFea()


def add_ufo_glyphs(ufo_font, bdf_font):
    units_per_element_x = get_units_per_element_x(bdf_font)

    add_element_glyph(ufo_font, bdf_font)

    anchors = {}

    for composed_name in bdf_font.glyphs:
        composed_glyph = bdf_font.glyphs[composed_name]

        ufo_glyph = ufo_font.newGlyph(composed_name)
        if composed_glyph.codepoint != 0:
            ufo_glyph.unicode = composed_glyph.codepoint
        ufo_glyph.width = int(composed_glyph.advance * units_per_element_x)

        components = decompose_bdf_glyph(bdf_font, composed_name)

        if len(components) == 0:
            add_ufo_bitmap(ufo_glyph, bdf_font, composed_glyph)

        else:
            add_ufo_components(ufo_glyph, bdf_font, components)

            add_anchors(anchors, bdf_font,
                        composed_glyph.codepoint, components)

    set_ufo_anchors(ufo_font, bdf_font, anchors)


def get_masters(bdf_font):
    masters = []

    masters_num = len(bdf_font.variable_axes)

    if masters_num >= 1:
        for master_index in range(2 ** masters_num):
            master = Object()
            master.name = ''
            master.location = {}

            for axis_index in range(masters_num):
                axis = bdf_font.variable_axes[axis_index]

                if not master_index & (1 << axis_index):
                    master.name += axis + 'min'
                    master.location[axis] = axes_info[axis]['min']
                else:
                    master.name += axis + 'max'
                    master.location[axis] = axes_info[axis]['max']

            masters.append(master)

    else:
        master = Object()
        master.name = ''
        master.location = {}

        masters.append(master)

    return masters


def write_designspace(path, bdf_font):
    font_file_name = get_file_name(bdf_font)

    designspace_filename = font_file_name + '.designspace'

    doc = fontTools.designspaceLib.DesignSpaceDocument()

    for axis in bdf_font.variable_axes:
        doc.addAxisDescriptor(
            tag=axis,
            name=axes_info[axis]['name'],
            minimum=int(100 * axes_info[axis]['min']),
            maximum=int(100 * axes_info[axis]['max']),
            default=int(100 * axes_info[axis]['default']),
        )

    for master in get_masters(bdf_font):
        master_file_name = get_file_name(bdf_font, master.name)

        location = {}
        for axis in master.location:
            axis_name = axes_info[axis]['name']

            location[axis_name] = int(100 * master.location[axis])

        doc.addSourceDescriptor(
            filename=master_file_name + '.ufo',
            name=master_file_name,
            familyName=bdf_font.family_name,
            location=location)

    for instance in bdf_font.variable_instances:
        instance_file_name = get_file_name(bdf_font, instance.name)

        location = {}
        for axis in instance.location:
            axis_name = axes_info[axis]['name']

            location[axis_name] = int(100 * instance.location[axis])

        doc.addInstanceDescriptor(
            filename=instance_file_name + '.ufo',
            name=instance_file_name,
            familyName=bdf_font.family_name,
            styleName=get_style_name(bdf_font, instance.name),
            location=location
        )

    doc.write(path + '/' + designspace_filename)

    # config.yaml
    config = open(path + '/' + font_file_name + '-config.yaml', 'wt')
    config.write('sources:\n')
    config.write('  - ' + designspace_filename + '\n')
    if len(bdf_font.variable_axes) > 0:
        config.write('axisOrder:\n')
        for axis in bdf_font.variable_axes:
            config.write(f'  - {axis}\n')
        config.close()


def main():
    global log_level

    parser = argparse.ArgumentParser(
        prog='bdf2ufo',
        description='Converts .bdf pixel fonts to .ufo static and variable vector fonts.')
    parser.add_argument('-V', '--version',
                        action='version',
                        version=f'bdf2ufo {bdf2ufo_version}')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='verbose mode')

    parser.add_argument('--family-name',
                        help='overrides the font family name string')
    parser.add_argument('--custom-style-name',
                        default='',
                        help='sets the font custom style name string')
    parser.add_argument('--font-version',
                        help='overrides the font version string')
    parser.add_argument('--weight',
                        type=int,
                        choices=[100, 200, 300, 400, 500,
                                 600, 700, 800, 900],
                        help='overrides the font weight ("Regular": 400)')
    parser.add_argument('--slope',
                        choices=['', 'Italic'],
                        help='overrides the font slope')
    parser.add_argument('--width-class',
                        type=int,
                        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9],
                        help='overrides the font width class ("Normal": 5)')

    parser.add_argument('--copyright',
                        help='overrides the font copyright string')
    parser.add_argument('--designer',
                        help='overrides the font designer string')
    parser.add_argument('--designer-url',
                        help='overrides the font designer URL string')
    parser.add_argument('--manufacturer',
                        help='overrides the font manufacturer string')
    parser.add_argument('--manufacturer-url',
                        help='overrides the font manufacturer URL string')
    parser.add_argument('--license',
                        help='overrides the font license string')
    parser.add_argument('--license-url',
                        help='overrides the font license URL string')

    parser.add_argument('--ascent',
                        type=int,
                        help='overrides the font ascent in pixels (baseline to top of line)')
    parser.add_argument('--descent',
                        type=int,
                        help='overrides the font descent in pixels (baseline to bottom of line)')
    parser.add_argument('--cap-height',
                        type=int,
                        help='overrides the font cap height in pixels (typically of uppercase A)')
    parser.add_argument('--x-height',
                        type=int,
                        help='overrides the font x height in pixels (typically of lowercase x)')

    parser.add_argument('--underline-position',
                        type=int,
                        help='sets the font underline position in pixels (top, relative to the baseline)')
    parser.add_argument('--underline-thickness',
                        type=int,
                        help='sets the font underline thickness in pixels')
    parser.add_argument('--strikeout-position',
                        type=int,
                        help='sets the font strikeout position in pixels (top, relative to the baseline)')
    parser.add_argument('--strikeout-thickness',
                        type=int,
                        help='sets the font strikeout thickness in pixels')

    parser.add_argument('--superscript-size',
                        type=int,
                        help='sets the font superscript size in pixels')
    parser.add_argument('--superscript-x',
                        type=int,
                        help='sets the font superscript x offset in pixels')
    parser.add_argument('--superscript-y',
                        type=int,
                        help='sets the font superscript y offset in pixels')
    parser.add_argument('--subscript-size',
                        type=int,
                        help='sets the font subscript size in pixels')
    parser.add_argument('--subscript-x',
                        type=int,
                        help='sets the font subscript x offset in pixels')
    parser.add_argument('--subscript-y',
                        type=int,
                        help='sets the font subscript y offset in pixels')

    parser.add_argument('--codepoint-subset',
                        default='',
                        help='specifies a comma-separated subset of Unicode characters to convert (e.g. 0x0-0x2000,0x20ee)')
    parser.add_argument('--notdef-codepoint',
                        type=auto_int,
                        help='specifies the codepoint for the .notdef character')
    parser.add_argument('--glyph-offset-x',
                        type=float,
                        default=0,
                        help='sets the glyphs x offset in pixels')
    parser.add_argument('--glyph-offset-y',
                        type=float,
                        default=0,
                        help='sets the glyphs y offset in pixels')
    parser.add_argument('--random-seed',
                        type=int,
                        default=0,
                        help='sets the random seed for the EJIT axis (see below)')
    parser.add_argument('--units-per-em',
                        type=int,
                        default=2048,
                        help='sets the units per em value')

    parser.add_argument('--variable-axes',
                        help='builds a variable font with specified axes (ESIZ: element size, ROND: roundness, BLED: bleed, XESP: horizontal element spacing, EJIT: element jitter): [axis][,...]')
    parser.add_argument('--variable-instance',
                        action='append',
                        help='builds a variable font instance with specified location: [family-subname][,[axis]=[value]][,...]')
    parser.add_argument('--static-axes',
                        help='sets the static axes: [[axis]=[value]][,...]')

    parser.add_argument('input',
                        help='the .bdf file to be converted')
    parser.add_argument('output',
                        help='the masters folder with the built .ufo files')

    config = parser.parse_args()

    if config.verbose:
        log_level = 0
    if config.variable_instance is None:
        config.variable_instance = []
    elif config.variable_axes is None:
        log_error(
            'can\'t create variable font instances without variable font axes')

    print('Loading BDF font...')
    bdf_font = load_bdf(config)

    print('Preparing masters folder...')
    os.makedirs(config.output, exist_ok=True)

    for master in get_masters(bdf_font):
        random.seed(config.random_seed)

        ufo_file_name = get_file_name(bdf_font, master.name) + '.ufo'

        for axis in master.location:
            bdf_font.location[axis] = master.location[axis]

        print(f'Building {ufo_file_name}...')

        ufo_font = ufoLib2.Font()
        set_ufo_info(ufo_font, bdf_font)

        add_ufo_glyphs(ufo_font, bdf_font)

        output_path = config.output + '/' + ufo_file_name

        if os.path.exists(output_path):
            shutil.rmtree(output_path)
        ufo_font.write(fontTools.ufoLib.UFOWriter(output_path))

    file_name = get_file_name(bdf_font)

    print(f'Building {file_name}.designspace and {file_name}-config.yaml...')
    write_designspace(config.output, bdf_font)

    print('Done.')


if __name__ == '__main__':
    main()
