#!/usr/bin/env python3
"""
Simple benchmark to measure OCR + parsing quality on a PDF.

Usage:
  python scripts/benchmark.py /path/to/file.pdf
"""

import sys
import time
from pathlib import Path

from ai_engine.ocr import OCRProcessor
from ai_engine.parser import ContractParser


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/benchmark.py /path/to/file.pdf")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    ocr = OCRProcessor()
    t0 = time.time()
    text, conf, scanned = ocr.extract_text_from_file(str(pdf_path))
    t_ocr = time.time() - t0

    parser = ContractParser()
    t1 = time.time()
    sections, metadata = parser.parse(text)
    t_parse = time.time() - t1

    print({
        "file": str(pdf_path),
        "scanned": scanned,
        "ocr_confidence": round(conf, 3),
        "chars": len(text),
        "words": len(text.split()),
        "language": metadata.language,
        "sections_count": len(sections),
        "ocr_time_s": round(t_ocr, 2),
        "parse_time_s": round(t_parse, 2),
    })

    # Show found sections' titles
    for s in sections:
        title = s.title.replace("\n", " ")[:120]
        print(f" - {s.section_type.value}: {title}")


if __name__ == "__main__":
    main()
