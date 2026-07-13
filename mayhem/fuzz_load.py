#!/usr/bin/env python3
"""Atheris libFuzzer harness for python-pptx (target: load-fuzz).

Drives python-pptx's document-loading path end to end: the fuzzer input is fed
verbatim as the bytes of a .pptx (OPC/ZIP) package to `pptx.Presentation()`, so
mutation exercises the ZIP container reader, the OPC part/relationship graph, and
the lxml-backed XML parsing of the presentation/slide parts.

`atheris.instrument_imports(include=["pptx"])` instruments the whole `pptx`
package so libFuzzer gets real edge coverage of the parsing code.

Exceptions that represent python-pptx *gracefully rejecting* obviously-invalid
input (a non-ZIP blob, a truncated archive, malformed XML, an undecodable part)
are swallowed so the fuzzer keeps exploring deeper document structure; anything
else propagates and is reported as a genuine defect.
"""
import io
import logging
import sys
import zlib
from zipfile import BadZipFile

import atheris

with atheris.instrument_imports(include=["pptx"]):
    import pptx
    from pptx.exc import PythonPptxError

from lxml.etree import LxmlError

# python-pptx logs on some malformed inputs; keep the fuzz output quiet.
logging.disable(logging.CRITICAL)


@atheris.instrument_func
def TestOneInput(data):
    try:
        pptx.Presentation(io.BytesIO(bytes(data)))
    except (
        PythonPptxError,
        BadZipFile,
        KeyError,
        zlib.error,
        NotImplementedError,
        UnicodeDecodeError,
        EOFError,
        LxmlError,
    ):
        return -1
    except ValueError as e:
        # BytesIO seek/negative-size rejections on truncated archives are expected.
        if "seek" in str(e) or "negative" in str(e):
            return -1
        raise


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
