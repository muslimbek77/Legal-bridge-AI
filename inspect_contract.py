import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.contracts.models import Contract

try:
    contract_id = 'b5640632-67c8-4391-b185-ced1d1abb981'
    contract = Contract.objects.get(id=contract_id)
    print(f"Contract ID: {contract.id}")
    print(f"Language: {contract.language}")
    
    text = contract.extracted_text
    print("\n--- Extracted Text Preview (First 2000 chars) ---")
    print(text[:2000])
    print("\n--- End Preview ---")

    # Save to file for easy reading
    with open('debug_contract_text.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Full text saved to debug_contract_text.txt")

except Contract.DoesNotExist:
    print(f"Contract {contract_id} not found.")
except Exception as e:
    print(f"Error: {e}")
