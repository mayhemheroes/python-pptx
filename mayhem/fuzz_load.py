#!/usr/bin/python3
from zipfile import BadZipFile

import atheris
import logging
import sys
import io

with atheris.instrument_imports():
    import pptx

# No logging
logging.disable(logging.CRITICAL)


@atheris.instrument_func
def TestOneInput(data):
    try:
        # Prepend package magic bytes
        pptx_data = b"PK\05\06" + data
        pptx.Presentation(io.BytesIO(pptx_data))
    except (pptx.exc.PythonPptxError, BadZipFile):
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
