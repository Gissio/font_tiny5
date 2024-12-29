# BDF2UFO
# Converts a .bdf pixel font to a .ufo variable vector font
#
# (C) 2024 Gissio
#
# License: MIT
#

import argparse
from datetime import datetime
import math
import os
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
bdf2ufo_version = '1.0'

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

slope_name_from_slant = {
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
    0x1f02: '03b1 0313 0300',
    0x1f03: '03b1 0314 0300',
    0x1f04: '03b1 0313 0301',
    0x1f05: '03b1 0314 0301',
    0x1f0a: '0391 0313 0300',
    0x1f0b: '0391 0314 0300',
    0x1f0c: '0391 0313 0301',
    0x1f0d: '0391 0314 0301',
    0x1f12: '03b5 0313 0300',
    0x1f13: '03b5 0314 0300',
    0x1f14: '03b5 0313 0301',
    0x1f15: '03b5 0314 0301',
    0x1f1a: '0395 0313 0300',
    0x1f1b: '0395 0314 0300',
    0x1f1c: '0395 0313 0301',
    0x1f1d: '0395 0314 0301',
    0x1f22: '03b7 0313 0300',
    0x1f23: '03b7 0314 0300',
    0x1f24: '03b7 0313 0301',
    0x1f25: '03b7 0314 0301',
    0x1f2a: '0397 0313 0300',
    0x1f2b: '0397 0314 0300',
    0x1f2c: '0397 0313 0301',
    0x1f2d: '0397 0314 0301',
    0x1f32: '03b9 0313 0300',
    0x1f33: '03b9 0314 0300',
    0x1f34: '03b9 0313 0301',
    0x1f35: '03b9 0314 0301',
    0x1f3a: '0399 0313 0300',
    0x1f3b: '0399 0314 0300',
    0x1f3c: '0399 0313 0301',
    0x1f3d: '0399 0314 0301',
    0x1f42: '03bf 0313 0300',
    0x1f43: '03bf 0314 0300',
    0x1f44: '03bf 0313 0301',
    0x1f45: '03bf 0314 0301',
    0x1f4a: '039f 0313 0300',
    0x1f4b: '039f 0314 0300',
    0x1f4c: '039f 0313 0301',
    0x1f4d: '039f 0314 0301',
    0x1f52: '03c5 0313 0300',
    0x1f53: '03c5 0314 0300',
    0x1f54: '03c5 0313 0301',
    0x1f55: '03c5 0314 0301',
    0x1f5b: '03a5 0314 0300',
    0x1f5d: '03a5 0314 0301',
    0x1f62: '03c9 0313 0300',
    0x1f63: '03c9 0314 0300',
    0x1f64: '03c9 0313 0301',
    0x1f65: '03c9 0314 0301',
    0x1f6a: '03a9 0313 0300',
    0x1f6b: '03a9 0314 0300',
    0x1f6c: '03a9 0313 0301',
    0x1f6d: '03a9 0314 0301',
    0x1fbe: '037a',
    0x1fc1: '0308 0342',
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

designspace_configurations = [
    ('Thin Square NoBleed', 0.1, 0, 0),
    ('Thick Square NoBleed', 1, 0, 0),
    ('Thin Round NoBleed', 0.1, 1, 0),
    ('Thick Round NoBleed', 1, 1, 0),
    ('Thin Square Bleed', 0.1, 0, 1),
    ('Thick Square Bleed', 1, 0, 1),
    ('Thin Round Bleed', 0.1, 1, 1),
    ('Thick Round Bleed', 1, 1, 1),
]


def log_info(message):
    if log_level <= 0:
        print("info: " + message)


def log_warning(message):
    if log_level <= 1:
        print("warning: " + message)


def get_unicode_string(codepoint):
    return 'U+' + f'{codepoint:04x}'


def get_decomposition_string(decomposition):
    return ', '.join([get_unicode_string(codepoint) for codepoint in decomposition])


def match_codepoint(codepoint_range, codepoint):
    if codepoint_range == '':
        codepoint_range = '0-0xffffffff'

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


def get_bdf_property(bdf, key, default):
    key = key.encode('utf-8')
    if key in bdf.properties:
        value = bdf.properties[key]
        if isinstance(value, int):
            return value
        else:
            return value.decode('utf-8')
    else:
        return default


def filter_name(name):
    return ''.join([c for c in name.lower() if c.isalpha()])


def load_bdf(path, config):
    bdf_boundingbox0 = [sys.maxsize, sys.maxsize]
    bdf_boundingbox1 = [-sys.maxsize, -sys.maxsize]

    with open(path, "rb") as handle:
        bdf = bdflib.reader.read_bdf(handle)

        # Load glyphs
        bdf_glyphs = {}
        bdf_codepoints = {}

        codepoint_subset = ''

        cap_height = 0
        x_height = 0

        for bdf_glyph in bdf.glyphs:
            # Extract properties
            codepoint = bdf_glyph.codepoint

            if codepoint == 0:
                name = '.notdef'
            else:
                if 'codepoint_subset' in config:
                    codepoint_subset = config['codepoint_subset']

                    if not match_codepoint(codepoint_subset, codepoint):
                        continue

                name = bdf_glyph.name.decode('utf-8')

                if not name[0].isalnum():
                    name = '_' + name

            name = ''.join(
                [c if (c.isalnum() or c == '.') else '_' for c in name])

            while name in bdf_glyphs:
                name += '_'

            advance = bdf_glyph.advance

            # Build bitmap
            bitmap = np.zeros((bdf_glyph.bbH, bdf_glyph.bbW), np.uint8)
            for y in range(bdf_glyph.bbH):
                value = bdf_glyph.data[y]
                for x in range(0, bdf_glyph.bbW):
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

            # Build glyph
            bdf_glyph = {
                'codepoint': codepoint,
                'bitmap': bitmap,
                'offset': boundingbox0,
                'advance': advance,
            }

            if codepoint == 0x58:
                cap_height = bitmap.shape[0]
            elif codepoint == 0x78:
                x_height = bitmap.shape[0]

            bdf_glyphs[name] = bdf_glyph
            bdf_codepoints[codepoint] = name

        # Add undefined combining glyphs
        for combining_codepoint in combining_infos:
            _, _, modifier_codepoint = combining_infos[combining_codepoint]

            if modifier_codepoint in bdf_codepoints and\
                    combining_codepoint not in bdf_codepoints and\
                match_codepoint(codepoint_subset, combining_codepoint):
                modifier_name = bdf_codepoints[modifier_codepoint]
                modifier_glyph = bdf_glyphs[modifier_name]

                combining_name = f'uni{combining_codepoint:04x}'
                combining_glyph = {
                    'codepoint': combining_codepoint,
                    'bitmap': modifier_glyph['bitmap'],
                    'offset': modifier_glyph['offset'],
                    'advance': modifier_glyph['advance'],
                }

                bdf_glyphs[combining_name] = combining_glyph
                bdf_codepoints[combining_codepoint] = combining_name

        if cap_height == 0:
            cap_height = bdf.ptSize
        if x_height == 0:
            x_height = bdf.ptSize

        # Font info
        version = get_bdf_property(
            bdf, 'FONT_VERSION', '')
        version_components = version.split('.')
        version_major, version_minor = (1, 0)
        if len(version_components) == 2:
            try:
                version_major, version_minor = (
                    int(version_components[0]), int(version_components[1]))
            except:
                pass

        family_name = get_bdf_property(
            bdf, 'FAMILY_NAME', bdf.name.decode('utf-8'))
        weight_name = filter_name(get_bdf_property(
            bdf, 'WEIGHT_NAME', ''))
        if weight_name in weight_from_weight_name:
            weight = weight_from_weight_name[weight_name]
        else:
            weight = 400
        slant = get_bdf_property(
            bdf, 'SLANT', '').upper()
        if slant in slope_name_from_slant:
            slope_name = slope_name_from_slant[slant]
        else:
            slope_name = ''
        setwidth_name = filter_name(get_bdf_property(
            bdf, 'SETWIDTH_NAME', ''))
        if setwidth_name in width_class_from_setwidth_name:
            width_class = width_class_from_setwidth_name[setwidth_name]
        else:
            width_class = 5

        style_name = weight_name_from_weight[weight]
        if slope_name != '':
            style_name += ' ' + slope_name
        if width_class != 5:
            style_name += ' ' + width_name_from_width_class[width_class]

        copyright = get_bdf_property(
            bdf, 'COPYRIGHT', '\n'.join([s.decode('utf-8')
                                         for s in bdf.comments]))
        designer = ''
        designer_url = ''
        manufacturer = get_bdf_property(
            bdf, 'FOUNDRY', '')
        manufacturer_url = ''
        license = ''
        license_url = ''

        point_size = bdf.ptSize
        ascent = get_bdf_property(
            bdf, 'FONT_ASCENT', point_size)
        descent = get_bdf_property(
            bdf, 'FONT_DESCENT', 0)
        cap_height = get_bdf_property(
            bdf, 'CAP_HEIGHT', cap_height)
        x_height = get_bdf_property(
            bdf, 'X_HEIGHT', x_height)
        underline_position = get_bdf_property(
            bdf, 'UNDERLINE_POSITION', 0)
        underline_thickness = get_bdf_property(
            bdf, 'UNDERLINE_THICKNESS', 0)
        strikeout_position = get_bdf_property(
            bdf, 'STRIKEOUT_ASCENT', 0)
        strikeout_thickness = get_bdf_property(
            bdf, 'STRIKEOUT_DESCENT', 0)
        superscript_size = get_bdf_property(
            bdf, 'SUPERSCRIPT_SIZE', None)
        superscript_x = get_bdf_property(
            bdf, 'SUPERSCRIPT_X', None)
        superscript_y = get_bdf_property(
            bdf, 'SUPERSCRIPT_Y', None)
        subscript_size = get_bdf_property(
            bdf, 'SUBSCRIPT_SIZE', None)
        subscript_x = get_bdf_property(
            bdf, 'SUBSCRIPT_X', None)
        subscript_y = get_bdf_property(
            bdf, 'SUBSCRIPT_Y', None)

        units_per_em = 1024

        if 'family_name' in config:
            family_name = config['family_name']
        if 'version' in config:
            version = config['version']
        if 'weight' in config:
            weight = config['weight']
        if 'slope_name' in config:
            slope_name = config['slope_name']
        if 'width_class' in config:
            width_class = config['width_class']

        if 'copyright' in config:
            copyright = config['copyright']
        if 'designer' in config:
            designer = config['designer']
        if 'designer_url' in config:
            designer_url = config['designer_url']
        if 'manufacturer' in config:
            manufacturer = config['manufacturer']
        if 'manufacturer_url' in config:
            manufacturer_url = config['manufacturer_url']
        if 'license' in config:
            license = config['license']
        if 'license_url' in config:
            license_url = config['license_url']

        if 'ascent' in config:
            ascent = config['ascent']
        if 'descent' in config:
            descent = config['descent']
        if 'cap_height' in config:
            cap_height = config['cap_height']
        if 'x_height' in config:
            x_height = config['x_height']
        if 'underline_position' in config:
            underline_position = config['underline_position']
        if 'underline_thickness' in config:
            underline_thickness = config['underline_thickness']
        if 'strikeout_position' in config:
            strikeout_position = config['strikeout_position']
        if 'strikeout_thickness' in config:
            strikeout_thickness = config['strikeout_thickness']
        if 'units_per_em' in config:
            units_per_em = config['units_per_em']

        if superscript_size == None:
            superscript_size = int(0.6 * cap_height)
        if superscript_x == None:
            superscript_x = cap_height - superscript_size
        if superscript_y == None:
            superscript_y = cap_height - superscript_size
        if subscript_size == None:
            subscript_size = int(0.6 * cap_height)
        if subscript_x == None:
            subscript_x = cap_height - subscript_size
        if subscript_y == None:
            subscript_y = cap_height - subscript_size

        units_per_pixel = int(units_per_em / point_size)

        bdf_font = {}
        bdf_font['version'] = version
        bdf_font['version_major'] = version_major
        bdf_font['version_minor'] = version_minor
        bdf_font['family_name'] = family_name
        bdf_font['weight'] = weight
        bdf_font['slope_name'] = slope_name
        bdf_font['width_class'] = width_class
        bdf_font['style_name'] = style_name
        bdf_font['font_name'] = family_name + ' ' + style_name

        bdf_font['copyright'] = copyright
        bdf_font['designer'] = designer
        bdf_font['designer_url'] = designer_url
        bdf_font['manufacturer'] = manufacturer
        bdf_font['manufacturer_url'] = manufacturer_url
        bdf_font['license'] = license
        bdf_font['license_url'] = license_url

        bdf_font['boundingbox'] = (bdf_boundingbox0, bdf_boundingbox1)
        bdf_font['ascent'] = ascent
        bdf_font['descent'] = descent
        bdf_font['cap_height'] = cap_height
        bdf_font['x_height'] = x_height
        bdf_font['underline_position'] = underline_position
        bdf_font['underline_thickness'] = underline_thickness
        bdf_font['strikeout_position'] = strikeout_position
        bdf_font['strikeout_thickness'] = strikeout_thickness
        bdf_font['superscript_x'] = superscript_x
        bdf_font['superscript_y'] = superscript_y
        bdf_font['superscript_size'] = superscript_size
        bdf_font['subscript_x'] = subscript_x
        bdf_font['subscript_y'] = subscript_y
        bdf_font['subscript_size'] = subscript_size

        bdf_font['units_per_em'] = units_per_em
        bdf_font['units_per_pixel'] = units_per_pixel

        bdf_font['glyphs'] = bdf_glyphs
        bdf_font['codepoints'] = bdf_codepoints

        return bdf_font


def add_offset(a, b):
    return (a[0] + b[0], a[1] + b[1])


def subtract_offset(a, b):
    return (a[0] - b[0], a[1] - b[1])


def set_ufo_info(ufo_font, bdf_font):
    # Calculations
    version = bdf_font['version']
    version_major = bdf_font['version_major']
    version_minor = bdf_font['version_minor']

    family_name = bdf_font['family_name']
    weight = bdf_font['weight']
    width_class = bdf_font['width_class']
    style_name = bdf_font['style_name']
    font_name = bdf_font['font_name']
    if weight <= 500:
        style_map_style_name = 'regular'
    else:
        style_map_style_name = 'bold'
    if bdf_font['slope_name'] != '':
        italic_angle = -15.0
        if style_map_style_name != '':
            style_map_style_name += ' '
        style_map_style_name += 'italic'
    else:
        italic_angle = 0.0

    copyright = bdf_font['copyright']
    designer = bdf_font['designer']
    designer_url = bdf_font['designer_url']
    manufacturer = bdf_font['manufacturer']
    manufacturer_url = bdf_font['manufacturer_url']
    license = bdf_font['license']
    license_url = bdf_font['license_url']
    unique_id = manufacturer + ': ' + font_name

    units_per_em = bdf_font['units_per_em']
    units_per_pixel = bdf_font['units_per_pixel']

    line_ascender = bdf_font['ascent'] * units_per_pixel
    line_descender = -bdf_font['descent'] * units_per_pixel
    line_height = line_ascender - line_descender
    em_descender = line_descender - int((units_per_em - line_height) / 2)
    em_ascender = units_per_em + em_descender
    boundingbox_ascender = max(
        bdf_font['boundingbox'][1][0] * units_per_pixel, 0)
    boundingbox_descender = max(
        -bdf_font['boundingbox'][0][0] * units_per_pixel, 0)
    cap_height = bdf_font['cap_height'] * units_per_pixel
    x_height = bdf_font['x_height'] * units_per_pixel
    underline_position = bdf_font['underline_position'] * units_per_pixel
    underline_thickness = bdf_font['underline_thickness'] * units_per_pixel
    strikeout_position = bdf_font['strikeout_position'] * units_per_pixel
    strikeout_thickness = bdf_font['strikeout_thickness'] * units_per_pixel
    superscript_x = bdf_font['superscript_x'] * units_per_pixel
    superscript_y = bdf_font['superscript_y'] * units_per_pixel
    superscript_size = int(
        bdf_font['superscript_size'] / bdf_font['cap_height'] * units_per_em)
    subscript_x = bdf_font['subscript_x'] * units_per_pixel
    subscript_y = bdf_font['subscript_y'] * units_per_pixel
    subscript_size = int(
        bdf_font['subscript_size'] / bdf_font['cap_height'] * units_per_em)

    current_date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    # Set UFO info
    ufo_info = ufo_font.info

    ufo_info.familyName = family_name
    ufo_info.styleName = style_name
    ufo_info.styleMapFamilyName = font_name
    ufo_info.styleMapStyleName = style_map_style_name
    ufo_info.versionMajor = version_major
    ufo_info.versionMinor = version_minor
    ufo_info.copyright = copyright
    ufo_info.unitsPerEm = units_per_em
    ufo_info.ascender = em_ascender
    ufo_info.descender = em_descender
    ufo_info.xHeight = x_height
    ufo_info.capHeight = cap_height
    ufo_info.italicAngle = italic_angle
    ufo_info.guidelines = []

    ufo_info.postscriptFontName = font_name.replace(' ', '-')
    ufo_info.postscriptFullName = font_name
    ufo_info.postscriptUnderlinePosition = underline_position
    ufo_info.postscriptUnderlineThickness = underline_thickness
    ufo_info.postscriptWeightName = weight_name_from_weight[weight]

    ufo_info.openTypeHeadCreated = current_date
    ufo_info.openTypeHheaAscender = line_ascender
    ufo_info.openTypeHheaDescender = line_descender
    ufo_info.openTypeHheaLineGap = 0

    ufo_info.openTypeNameVersion = "Version " + version
    ufo_info.openTypeNameUniqueID = unique_id
    ufo_info.openTypeNameCompatibleFullName = ufo_info.styleMapFamilyName
    ufo_info.openTypeNameDesigner = designer
    ufo_info.openTypeNameDesignerURL = designer_url
    ufo_info.openTypeNameManufacturer = manufacturer
    ufo_info.openTypeNameManufacturerURL = manufacturer_url
    ufo_info.openTypeNameLicense = license
    ufo_info.openTypeNameLicenseURL = license_url

    ufo_info.openTypeOS2WeightClass = weight
    ufo_info.openTypeOS2WidthClass = width_class
    ufo_info.openTypeOS2VendorID = "B2UF"
    ufo_info.openTypeOS2Type = []
    ufo_info.openTypeOS2Panose = [2, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ufo_info.openTypeOS2FamilyClass = [0, 0]
    # info.openTypeOS2UnicodeRanges = ...
    ufo_info.openTypeOS2TypoAscender = ufo_info.ascender
    ufo_info.openTypeOS2TypoDescender = ufo_info.descender
    ufo_info.openTypeOS2TypoLineGap = ufo_info.openTypeHheaLineGap
    ufo_info.openTypeOS2WinAscent = boundingbox_ascender
    ufo_info.openTypeOS2WinDescent = boundingbox_descender
    ufo_info.openTypeOS2SubscriptXSize = subscript_size
    ufo_info.openTypeOS2SubscriptYSize = subscript_size
    ufo_info.openTypeOS2SubscriptXOffset = subscript_x
    ufo_info.openTypeOS2SubscriptYOffset = subscript_y
    ufo_info.openTypeOS2SuperscriptXSize = superscript_size
    ufo_info.openTypeOS2SuperscriptYSize = superscript_size
    ufo_info.openTypeOS2SuperscriptXOffset = superscript_x
    ufo_info.openTypeOS2SuperscriptYOffset = superscript_y
    ufo_info.openTypeOS2StrikeoutPosition = strikeout_position
    ufo_info.openTypeOS2StrikeoutSize = strikeout_thickness


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
    bdf_codepoints = bdf_font['codepoints']

    # composed_codepoint = composed_glyph['codepoint']
    composed_bitmap = composed_glyph['bitmap']

    if not isinstance(bitmap, np.ndarray):
        bitmap = np.zeros(composed_bitmap.shape, np.uint8)

    if len(decomposition) == 0:
        if (composed_bitmap == bitmap).all():
            return []

        return 'mismatch'

    component_codepoint = decomposition[0]

    for stage in range(2):
        if stage == 0:
            if component_codepoint not in bdf_codepoints:
                continue

        else:
            if component_codepoint not in combining_infos:
                break

            _, _, modifier_codepoint = combining_infos[component_codepoint]

            if modifier_codepoint == composed_glyph['codepoint']:
                return 'uncomposable'

            if modifier_codepoint not in bdf_codepoints:
                return 'missing'

            component_codepoint = modifier_codepoint

        component_name = bdf_codepoints[component_codepoint]
        component_glyph = bdf_font['glyphs'][component_name]
        component_bitmap = component_glyph['bitmap']

        delta_size = subtract_offset(
            composed_bitmap.shape, component_bitmap.shape)

        for offset_y in range(delta_size[0] + 1):
            for offset_x in range(delta_size[1] + 1):
                offset = (offset_y, offset_x)
                bitmap_copy = bitmap.copy()

                if not paint_bdf_glyph(composed_bitmap,
                                       component_bitmap,
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
                    bdf_components.append({
                        'name': component_name,
                        'offset': add_offset(composed_glyph['offset'], offset)
                    })

                    return bdf_components

    if component_codepoint not in bdf_codepoints:
        return 'missing'

    else:
        return 'mismatch'


def decompose_bdf_glyph(bdf_font, composed_name):
    composed_glyph = bdf_font['glyphs'][composed_name]
    composed_codepoint = composed_glyph['codepoint']

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


def get_points(units_per_pixel,
               pixel_volume,
               pixel_roundness,
               pixel_bleed):
    pixel_unit = units_per_pixel / 2
    unit = pixel_volume * pixel_unit
    radius = pixel_roundness * unit

    # Cubic curves
    tangent = radius * (4 / 3) * math.tan(math.radians(90 / 4))
    max_x = unit + pixel_bleed * (2 * pixel_unit - unit)
    max_y = unit
    min_x = max_x - radius
    min_y = max_y - radius
    tangent_x = min_x + tangent
    tangent_y = min_y + tangent

    return [
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
    # max_x = unit + pixel_bleed * (2 * pixel_unit - unit)
    # max_y = unit
    # min_x = max_x - radius
    # min_y = max_y - radius
    # tangent_x = min_x + tangent
    # tangent_y = min_y + tangent
    # midarc_x = min_x + midarc
    # midarc_y = min_y + midarc

    # return [
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


def add_ufo_bitmap(ufo_glyph,
                   bdf_font,
                   bdf_glyph):
    units_per_pixel = bdf_font['units_per_pixel']

    bdf_bitmap = bdf_glyph['bitmap']
    bdf_glyph_offset = bdf_glyph['offset']

    points = get_points(units_per_pixel,
                        bdf_font['pixel_volume'],
                        bdf_font['pixel_roundness'],
                        bdf_font['pixel_bleed'])

    for y in range(bdf_bitmap.shape[0]):
        for x in range(bdf_bitmap.shape[1]):
            if bdf_bitmap[y][x]:
                ufo_y = units_per_pixel * (bdf_glyph_offset[0] + y + 0.5)
                ufo_x = units_per_pixel * (bdf_glyph_offset[1] + x + 0.5)

                ufo_points = []
                for point_offset, point_type in points:
                    ufo_points.append(
                        ufoLib2.objects.Point(
                            int(ufo_x + point_offset[1]),
                            int(ufo_y + point_offset[0]),
                            point_type)
                    )
                ufo_contour = ufoLib2.objects.Contour(ufo_points)
                ufo_glyph.appendContour(ufo_contour)


def add_ufo_components(ufo_glyph,
                       bdf_font,
                       components):
    units_per_pixel = bdf_font['units_per_pixel']
    bdf_glyphs = bdf_font['glyphs']

    for component in components:
        component_name = component['name']
        component_offset = component['offset']

        ufo_component = ufoLib2.objects.Component(component_name)

        delta = subtract_offset(component_offset,
                                bdf_glyphs[component_name]['offset'])

        if delta != (0, 0):
            ufo_component.transformation = [
                1, 0, 0, 1,
                delta[1] * units_per_pixel,
                delta[0] * units_per_pixel]

        ufo_glyph.components.append(ufo_component)


def add_anchors(anchors,
                bdf_font,
                composed_codepoint,
                components):
    bdf_glyphs = bdf_font['glyphs']

    if composed_codepoint in custom_anchors:
        return

    if len(components) != 2:
        return

    # Get base and combining glyphs
    base_name = None
    combining_name = None

    for component in components:
        component_name = component['name']
        component_glyph = bdf_glyphs[component_name]
        component_codepoint = component_glyph['codepoint']

        if component_codepoint in combining_infos:
            combining_name = component_name
            combining_size = component_glyph['bitmap'].shape
            combining_glyph_offset = component_glyph['offset']
            combining_offset = component['offset']

            combining_info = combining_infos[component_codepoint]
            anchor_name = combining_info[1]

        else:
            base_name = component_name
            base_glyph_offset = component_glyph['offset']
            base_offset = component['offset']

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
                f'{get_unicode_string(composed_codepoint)} anchor "{anchor_name}"'
                ' does not align with anchors from components [' +
                ', '.join([x['name'] for x in components]) + ']'
            )


def set_ufo_anchors(ufo_font, bdf_font, anchors):
    units_per_pixel = bdf_font['units_per_pixel']
    bdf_glyphs = bdf_font['glyphs']
    bdf_codepoints = bdf_font['codepoints']

    # UFO anchors, base and mark lists
    mark_map = {}
    base_map = {}

    for component_name in anchors:
        component_codepoint = bdf_glyphs[component_name]['codepoint']

        component_anchors = anchors[component_name]
        ufo_glyph = ufo_font[component_name]

        for anchor_name in component_anchors:
            anchor_offset = component_anchors[anchor_name]

            anchor = ufoLib2.objects.Anchor(
                anchor_offset[1] * units_per_pixel,
                anchor_offset[0] * units_per_pixel,
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
    if 0x41 in bdf_codepoints:
        features.statements.append(
            fontTools.feaLib.ast.LanguageSystemStatement('latn', 'dflt'))
    if 0x391 in bdf_codepoints:
        features.statements.append(
            fontTools.feaLib.ast.LanguageSystemStatement('grek', 'dflt'))
    if 0x410 in bdf_codepoints:
        features.statements.append(
            fontTools.feaLib.ast.LanguageSystemStatement('cyrl', 'dflt'))

    # Mark definitions
    allmarks = fontTools.feaLib.ast.GlyphClass()
    topmarks = fontTools.feaLib.ast.GlyphClass()

    for codepoint in combining_infos:
        if codepoint in bdf_codepoints:
            allmarks.append(bdf_codepoints[codepoint])

            if combining_infos[codepoint][1] in ['top', 'top.shifted']:
                topmarks.append(bdf_codepoints[codepoint])

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
                    anchor_offset[1] * units_per_pixel,
                    anchor_offset[0] * units_per_pixel),
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
                        anchor_offset[1] * units_per_pixel,
                        anchor_offset[0] * units_per_pixel),
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
    bdf_glyphs = bdf_font['glyphs']
    units_per_pixel = bdf_font['units_per_pixel']

    anchors = {}

    for composed_name in bdf_glyphs:
        composed_glyph = bdf_glyphs[composed_name]
        composed_codepoint = composed_glyph['codepoint']
        composed_advance = composed_glyph['advance']

        ufo_glyph = ufo_font.newGlyph(composed_name)
        if composed_codepoint != 0:
            ufo_glyph.unicode = composed_codepoint
        ufo_glyph.width = composed_advance * units_per_pixel

        components = decompose_bdf_glyph(bdf_font, composed_name)

        if len(components) == 0:
            add_ufo_bitmap(ufo_glyph, bdf_font, composed_glyph)

        else:
            add_ufo_components(ufo_glyph, bdf_font, components)

            add_anchors(anchors, bdf_font, composed_codepoint, components)

    set_ufo_anchors(ufo_font, bdf_font, anchors)


def get_designspace_instance(family_name,
                             style_name,
                             volume,
                             roundness,
                             bleed):
    font_name = family_name + ' ' + style_name
    file_name = font_name.replace(' ', '-') + '.ufo'

    return fontTools.designspaceLib.InstanceDescriptor(
        filename=file_name,
        name=font_name,
        familyName=family_name,
        styleName=style_name,
        location={
            'Volume': volume,
            'Roundness': roundness,
            'Bleed': bleed,
        }
    )


def write_designspace(path, bdf_font):
    family_name = bdf_font['family_name']
    style_name = bdf_font['style_name']
    font_name = bdf_font['font_name']

    designspace_filename = font_name.replace(' ', '-') + '.designspace'
    designspace_path = path + '/' + designspace_filename

    doc = fontTools.designspaceLib.DesignSpaceDocument()

    doc.addAxisDescriptor(
        tag="VOLM",
        name="Volume",
        minimum=10,
        maximum=100,
        default=100,
    )

    doc.addAxisDescriptor(
        tag="ROND",
        name="Roundness",
        minimum=0,
        maximum=100,
        default=0,
    )

    doc.addAxisDescriptor(
        tag="BLED",
        name="Bleed",
        minimum=0,
        maximum=100,
        default=0,
    )

    for configuration in designspace_configurations:
        ufo_style_name = style_name + ' ' + configuration[0]
        ufo_font_name = family_name + ' ' + ufo_style_name
        ufo_file_name = ufo_font_name.replace(' ', '-')

        doc.addSourceDescriptor(
            filename=ufo_file_name + '.ufo',
            name=ufo_file_name,
            familyName=family_name,
            styleName=ufo_style_name,
            location={
                'Volume': int(100 * configuration[1]),
                'Roundness': int(100 * configuration[2]),
                'Bleed': int(100 * configuration[3]),
            })

    doc.addInstance(
        get_designspace_instance(family_name, style_name + '', 100, 0, 0))
    doc.addInstance(
        get_designspace_instance(family_name, style_name + ' LCD', 85, 0, 0))
    doc.addInstance(
        get_designspace_instance(family_name, style_name + ' DotMatrix', 85, 80, 0))
    doc.addInstance(
        get_designspace_instance(family_name, style_name + ' CRT', 70, 60, 60))

    doc.write(designspace_path)

    # config.yaml
    config_path = path + '/config.yaml'

    config = open(config_path, 'wt')
    config.write('sources:\n')
    config.write('  - ' + designspace_filename + '\n')
    config.write('axisOrder:\n')
    config.write('  - VOLM\n')
    config.write('  - ROND\n')
    config.write('  - BLED\n')
    config.close()


def main():
    global log_level

    parser = argparse.ArgumentParser(
        prog='bdf2ufo',
        description='Converts a .bdf pixel font to a .ufo vector font designspace with variable font support.')
    parser.add_argument('-V', '--version',
                        action='version',
                        version=f'bdf2ufo {bdf2ufo_version}')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='verbose mode')

    parser.add_argument('--units-per-em',
                        type=int,
                        help='sets the units per em value')
    parser.add_argument('--codepoints',
                        help='specifies a comma-separated subset of Unicode characters to convert (e.g. 0x0-0x2000,0x20ee).')

    parser.add_argument('--family-name',
                        help='overrides the font family name string')
    parser.add_argument('--font-version',
                        help='overrides the font version string')
    parser.add_argument('--weight',
                        type=int,
                        choices=[100, 200, 300, 400,
                                 500, 600, 700, 800, 900],
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
    parser.add_argument('--strikeout-position',
                        type=int,
                        help='sets the font strikeout position in pixels (top, relative to the baseline)')
    parser.add_argument('--strikeout-thickness',
                        type=int,
                        help='sets the font strikeout width in pixels')
    parser.add_argument('--underline-position',
                        type=int,
                        help='sets the font underline position in pixels (top, relative to the baseline)')
    parser.add_argument('--underline-thickness',
                        type=int,
                        help='sets the font underline width in pixels')

    parser.add_argument('input',
                        help='the .bdf file to be converted')
    parser.add_argument('output',
                        help='the project folder with the converted .ufo files')

    args = parser.parse_args()

    if args.verbose:
        log_level = 0

    config = {}

    if args.units_per_em != None:
        config['units_per_em'] = args.units_per_em
    if args.codepoints != None:
        config['codepoint_subset'] = args.codepoints

    if args.family_name != None:
        config['family_name'] = args.family_name
    if args.font_version != None:
        config['version'] = args.font_version
    if args.weight != None:
        config['weight'] = args.weight
    if args.slope != None:
        config['slope'] = args.slope
    if args.width_class != None:
        config['width_class'] = args.width_class

    if args.copyright != None:
        config['copyright'] = args.copyright
    if args.designer != None:
        config['designer'] = args.designer
    if args.designer_url != None:
        config['designer_url'] = args.designer_url
    if args.manufacturer != None:
        config['manufacturer'] = args.manufacturer
    if args.manufacturer_url != None:
        config['manufacturer_url'] = args.manufacturer_url
    if args.license != None:
        config['license'] = args.license
    if args.license_url != None:
        config['license_url'] = args.license_url

    if args.ascent != None:
        config['ascent'] = args.ascent
    if args.descent != None:
        config['descent'] = args.descent
    if args.cap_height != None:
        config['cap_height'] = args.cap_height
    if args.x_height != None:
        config['x_height'] = args.x_height
    if args.strikeout_position != None:
        config['strikeout_position'] = args.strikeout_position
    if args.strikeout_thickness != None:
        config['strikeout_thickness'] = args.strikeout_thickness
    if args.underline_position != None:
        config['underline_position'] = args.underline_position
    if args.underline_thickness != None:
        config['underline_thickness'] = args.underline_thickness

    print('Loading BDF font...')
    bdf_font = load_bdf(args.input, config)

    print('Preparing UFO designspace folder...')
    os.makedirs(args.output, exist_ok=True)

    for configuration in designspace_configurations:
        style_name = configuration[0]
        ufo_font_name = bdf_font['font_name'] + ' ' + style_name
        ufo_file_name = ufo_font_name.replace(' ', '-') + '.ufo'

        bdf_font['pixel_volume'] = configuration[1]
        bdf_font['pixel_roundness'] = configuration[2]
        bdf_font['pixel_bleed'] = configuration[3]

        print(f'Building {ufo_file_name}...')

        ufo_font = ufoLib2.Font()
        set_ufo_info(ufo_font, bdf_font)

        add_ufo_glyphs(ufo_font, bdf_font)

        output_path = args.output + '/' + ufo_file_name

        if os.path.exists(output_path):
            shutil.rmtree(output_path)
        ufo_font.write(fontTools.ufoLib.UFOWriter(output_path))

    print(f'Building designspace...')
    write_designspace(args.output, bdf_font)

    print('Done.')


if __name__ == '__main__':
    main()
