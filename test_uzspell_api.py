import requests
import json

def test_word(word):
    try:
        resp = requests.post('http://localhost:4000/api/spell', json={'word': word})
        print(f"Word: {word}, Status: {resp.status_code}, Response: {resp.text}")
    except Exception as e:
        print(f"Error checking {word}: {e}")

words = [
    "шартнома", # Correct
    "шартнма",  # Incorrect
    "билан",    # Correct
    "Тошкент",  # Correct
    "Республикаси" # Correct
]

print("Testing UzSpell API...")
for w in words:
    test_word(w)
