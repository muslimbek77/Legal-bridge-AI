#!/usr/bin/env python3
"""Test party name extraction patterns."""

import sys
sys.path.append('.')

from ai_engine.ocr import OCRProcessor
import re

# Extract text
result = OCRProcessor().extract_text_from_file('shartnomalar/G-18.pdf')
text = result[0] if isinstance(result, tuple) else result

print("=" * 80)
print("FIRST 2000 CHARS (for debugging)")
print("=" * 80)
print(text[:2000])
print()

# Test contract number
print("=" * 80)
print("CONTRACT NUMBER TEST")
print("=" * 80)
pattern_num = r"(?im)^\s*(?:ШАРТНОМA|ШАРТНОМА|SHARTNOMA|ДОГОВОР|CONTRACT)\s+(?:№|No|N)\.?\s*([\d\-/\А-Я]+)"
match_num = re.search(pattern_num, text)
if match_num:
    print(f"✓ Contract number: {match_num.group(1)}")
else:
    print("✗ Contract number: NO MATCH")
print()

# Test party A - from intro
print("=" * 80)
print("PARTY A TEST (intro clause)")
print("=" * 80)
# Pattern: "DORKOMPLEKTSNAB PLUS" МЧЖ номидан... «Буюртмачи» деб юритилади
# Try different quote styles
patterns_a = [
    r'"([^"]+)"\s*МЧЖ\s+номидан.*?(?:«|")\s*[Бб]уюртмачи\s*(?:»|")?\s+деб\s+юритилад',
    r'[""]([^"""]+)[""]\s*МЧЖ\s+номидан.*?[«"]\s*[Бб]уюртмачи\s*[»"]?\s+деб\s+юритилад',
    r'[""«]([А-ЯЁA-Z][^"""»]+?)[""»]\s*МЧЖ\s+номидан.*?[«"]\s*[Бб]уюртмачи',
]
found = False
for i, pattern_a in enumerate(patterns_a):
    match_a = re.search(pattern_a, text[:2000], re.IGNORECASE | re.DOTALL)
    if match_a:
        print(f"✓ Party A (pattern {i+1}): {match_a.group(1)}")
        found = True
        break
if not found:
    print("✗ Party A intro: NO MATCH")
    
# Test from requisites
pattern_a2 = r"(?im)БУЮРТМАЧИ.*?\n\s*([^\n]+)"
match_a2 = re.search(pattern_a2, text[-5000:])
if match_a2:
    print(f"✓ Party A (requisites): {match_a2.group(1)[:100]}")
else:
    print("✗ Party A requisites: NO MATCH")
print()

# Test party B - from intro
print("=" * 80)
print("PARTY B TEST (intro clause)")
print("=" * 80)
# Pattern: ва "EURO GLOBAL ASPHALT" МЧЖ номидан... «Етказиб берувчи» деб юритилади
patterns_b = [
    r'ва\s+"([^"]+)"\s*МЧЖ\s+номидан.*?[«"]\s*(?:етказиб\s+берувчи|ижрочи)\s*[»"]?\s+деб\s+юритилад',
    r'ва\s+["""]([^"""]+)["""]\s*МЧЖ\s+номидан.*?[«"]\s*(?:[Ее]тказиб\s+берувчи|[Ии]жрочи)\s*[»"]?\s+деб\s+юритилад',
    r'ва\s+[""«]([А-ЯЁA-Z][^"""»]+?)[""»]\s*МЧЖ\s+номидан.*?[«"]\s*(?:[Ее]тказиб\s+берувчи|[Ии]жрочи)',
]
found = False
for i, pattern_b in enumerate(patterns_b):
    match_b = re.search(pattern_b, text[:2000], re.IGNORECASE | re.DOTALL)
    if match_b:
        print(f"✓ Party B (pattern {i+1}): {match_b.group(1)}")
        found = True
        break
if not found:
    print("✗ Party B intro: NO MATCH")

# Test from requisites  
pattern_b2 = r"(?im)(?:ЕТКАЗИБ\s+БЕРУВЧИ|ИЖРОЧИ).*?\n\s*([^\n]+)"
match_b2 = re.search(pattern_b2, text[-5000:])
if match_b2:
    print(f"✓ Party B (requisites): {match_b2.group(1)[:100]}")
else:
    print("✗ Party B requisites: NO MATCH")
