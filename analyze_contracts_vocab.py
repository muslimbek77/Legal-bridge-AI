import os
import sys
import glob
from pathlib import Path
from collections import Counter
import hunspell

# Setup path
sys.path.append(str(Path(__file__).resolve().parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from ai_engine.ocr import OCRProcessor
from ai_engine.spelling import SpellingChecker
from ai_engine.spelling.backends import BackendResult

class FastHunspellBackend:
    def __init__(self):
        # paths are relative to workspace root
        base_path = Path('uzspell/dict').resolve()
        
        # Verify files exist
        cyrl_aff = base_path / 'cyrillic/uz_UZ_Cyrl.aff'
        cyrl_dic = base_path / 'cyrillic/uz_UZ_Cyrl.dic'
        latn_aff = base_path / 'latin/uz_UZ.aff'
        latn_dic = base_path / 'latin/uz_UZ.dic'
        
        if not cyrl_aff.exists():
            raise FileNotFoundError(f"Missing dictionary: {cyrl_aff}")

        # Note: hunspell order is (dic, aff) usually? Or (start, end)?
        # Checking python-hunspell docs or common usage: Hunspell(dic_path, aff_path) or vice versa?
        # usually Hunspell(word_dic, aff) or key.
        # But wait, usually it is Hunspell('path/to/dic_without_ext') or Hunspell('name', local_dir)
        # Let's try passing full paths.
        
        # According to 'hunspell' pypi package (cython): Hunspell(aff, dic)
        self.h_cyrl = hunspell.Hunspell(str(cyrl_aff), str(cyrl_dic))
        self.h_latn = hunspell.Hunspell(str(latn_aff), str(latn_dic))
        self._cache = {}

    def check(self, word: str, language: str) -> BackendResult:
        # Simple caching
        key = (word, language)
        if key in self._cache:
            return self._cache[key]

        is_correct = True
        suggestion = None
        
        # Select dictionary
        h = None
        if language == 'uz-cyrl':
            h = self.h_cyrl
        elif language == 'uz-latn':
            h = self.h_latn
        
        if h:
            try:
                # hunspell might need bytes, but usually strings work in python 3
                if not h.spell(word):
                    is_correct = False
            except Exception:
                pass

        res = BackendResult(correct=is_correct, suggestion=suggestion)
        self._cache[key] = res
        return res

def analyze_vocabulary():
    contracts_dir = Path('/home/rasulbek/muslim-projects/Legal-bridge-AI/shartnomalar')
    if not contracts_dir.exists():
        print(f"Directory not found: {contracts_dir}")
        return

    files = list(contracts_dir.glob('*.*'))
    
    ocr = OCRProcessor()
    checker = SpellingChecker()
    
    # SWAP BACKEND
    print("Initializing Fast Hunspell Backend...")
    try:
        fast_backend = FastHunspellBackend()
        checker._external = fast_backend
        print("Backend swapped successfully.")
    except Exception as e:
        print(f"Failed to init fast backend: {e}. Using default (slow).")
    
    all_errors = []
    
    print(f"Found {len(files)} files. Starting analysis...")
    
    for i, file_path in enumerate(files):
        if file_path.suffix.lower() not in ['.pdf', '.docx', '.doc', '.jpg', '.png']:
            continue
            
        print(f"\n[{i+1}/{len(files)}] Processing {file_path.name}...")
        try:
            text, conf, scanned = ocr.extract_text_from_file(file_path)
            
            # Use 'uz-cyrl' as default for now as requested
            errors = checker.check_text(text, language='uz-cyrl')
            
            error_words = [e.word.lower() for e in errors]
            all_errors.extend(error_words)
                
            print(f"  - Extracted {len(text)} chars. Found {len(errors)} potential errors.")
            
        except Exception as e:
            print(f"  - Failed to process: {e}")

    print("\n" + "="*50)
    print("TOP FREQUENT 'ERRORS' (Candidates for whitelist/fix)")
    print("="*50)
    
    counter = Counter(all_errors)
    for word, count in counter.most_common(100):
        print(f"{word}: {count}")

if __name__ == "__main__":
    analyze_vocabulary()
