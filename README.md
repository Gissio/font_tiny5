# tiny5

tiny5 is a variable-width, 5-pixel font playing with the concept of least amount of information that produces both legible and aesthetically pleasing text.

It is aimed at digital media such as websites, mobile apps and, especially, monochrome LCD displays.

Each of tiny5's glyphs was carefully crafted to be visually appealing and easy to read. tiny5 fully supports the Google Fonts Latin Plus and Latin African character set as well as Unicode blocks 0 to 2.

The font is also available in [BDF](https://en.wikipedia.org/wiki/Glyph_Bitmap_Distribution_Format) format for easy integration with the [mcu-renderer](https://github.com/Gissio/mcu-renderer), [u8g2](https://github.com/olikraus/u8g2) and [TFT_eSPI](https://github.com/Bodmer/TFT_eSPI) libraries.

## Overview

![tiny5 overview](documentation/overview.png)

## Sample

![tiny5 sample](documentation/sample.png)

## Changelog

### 1.001

* Added Google Fonts Latin Plus and Latin African character sets.
* Major corrections.

### 1.000

* First release.

## Build

With Python 3.10 or newer, install the `requirements.txt` and run this command:

    gftools builder sources/config.yaml

## Acknowledgements 

tiny5 was designed by Stefan Schmidt using [Bits'N'Picas](https://github.com/kreativekorp/bitsnpicas) and [FontForge](https://fontforge.org/).

More information about Stefan Schmidt at https://www.stefanschmidtart.com

## License

This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://scripts.sil.org/OFL
