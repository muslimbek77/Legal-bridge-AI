import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.spelling import SpellingChecker
from apps.contracts.models import Contract

try:
    contract_id = 'b5640632-67c8-4391-b185-ced1d1abb981'
    contract = Contract.objects.get(id=contract_id)
    text = contract.extracted_text
    
    checker = SpellingChecker()
    errors = checker.check_text(text, language="uz-cyrl")
    
    print(f"Detected Errors Count: {len(errors)}")
    print("\n--- Unique Error Words & Suggestions ---")
    seen = set()
    for err in errors:
        if err.word.lower() not in seen:
            print(f"'{err.word}' -> {err.suggestion} ({err.error_type.value})")
            seen.add(err.word.lower())

except Contract.DoesNotExist:
    print(f"Contract {contract_id} not found.")
except Exception as e:
    print(f"Error: {e}")
