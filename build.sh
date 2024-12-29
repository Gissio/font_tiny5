#!/bin/bash
if [ ! -d env ] ; then
  python -m venv env
fi

source env/bin/activate

pip install -r requirements.txt

python scripts/bdf2ufo.py --designer "Stefan Schmidt" --designer-url "https://github.com/Gissio/font_tiny5" --manufacturer "Stefan Schmidt Art" --manufacturer-url "https://www.stefanschmidtart.com/" --license "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org" --license-url "https://openfontlicense.org" --strikeout-position 2 --strikeout-thickness 1 --underline-position -2 --underline-thickness 1 fonts/bdf/Tiny5-Regular.bdf build
gftools builder build/config.yaml

python scripts/bdf2ufo.py --designer "Stefan Schmidt" --designer-url "https://github.com/Gissio/font_tiny5" --manufacturer "Stefan Schmidt Art" --manufacturer-url "https://www.stefanschmidtart.com/" --license "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org" --license-url "https://openfontlicense.org" --strikeout-position 2 --strikeout-thickness 1 --underline-position -2 --underline-thickness 1 fonts/bdf/Tiny5-Bold.bdf build
gftools builder build/config.yaml
