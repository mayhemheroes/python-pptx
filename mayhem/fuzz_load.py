#!/usr/bin/python3
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
        # Get two fuzzer python objects
        ppt_f = io.BytesIO(data)
        pptx.Presentation(ppt_f)
        ppt_f.close()
    except pptx.exc.PythonPptxError:
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
