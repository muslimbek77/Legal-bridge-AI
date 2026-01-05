import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_engine.ocr import OCRProcessor
from ai_engine.parser import ContractParser

path = os.environ.get('CONTRACT_PATH', 'shartnomalar/Договор (НК)_ 10 от 01.04.2025  (1).pdf')

if __name__ == '__main__':
    text, conf, scanned = OCRProcessor().extract_text_from_file(path)
    print('OCR ok. scanned=', scanned, 'conf=', conf)

    parser = ContractParser()
    sections, meta = parser.parse(text)

    print('party_a_inn:', meta.party_a_inn)
    print('party_b_inn:', meta.party_b_inn)
    print('party_a_name:', meta.party_a_name)
    print('party_b_name:', meta.party_b_name)
    print('amount:', meta.total_amount, meta.currency)
    print('language:', meta.language)

    # Debug: print windows around each INN
    import re
    def show_inn_window(inn):
        if not inn:
            return
        inn_pat = ''.join([f"{d}[\\s–-]*" for d in inn])
        m = re.search(inn_pat, text)
        if m:
            start = max(0, m.start() - 600)
            end = min(len(text), m.end() + 600)
            print(f"\n--- Window near INN {inn} ---\n")
            print(text[start:end])
            print("\n-----------------------------\n")
    show_inn_window(meta.party_a_inn)
    show_inn_window(meta.party_b_inn)
