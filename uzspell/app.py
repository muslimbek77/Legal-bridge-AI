import os
from flask import Flask, request, jsonify
import hunspell

app = Flask(__name__)

# Fayl yo'llari
DICT_PATH = os.path.join(os.path.dirname(__file__), 'dict')
LATIN_PATH = os.path.join(DICT_PATH, 'latin')
CYRILLIC_PATH = os.path.join(DICT_PATH, 'cyrillic')

# Hunspell obyektlari
hunspell_latin = hunspell.HunSpell(
    os.path.join(LATIN_PATH, 'uz_UZ.dic'),
    os.path.join(LATIN_PATH, 'uz_UZ.aff')
)
hunspell_cyrillic = hunspell.HunSpell(
    os.path.join(CYRILLIC_PATH, 'uz_UZ_Cyrl.dic'),
    os.path.join(CYRILLIC_PATH, 'uz_UZ_Cyrl.aff')
)
def detect_script(word):
    # Kirill harflari: U+0400 ... U+04FF
    for ch in word:
        if '\u0400' <= ch <= '\u04FF':
            return 'cyrillic'
    return 'latin'

@app.route('/api/spell', methods=['POST'])
def spell_check():
    data = request.get_json(force=True)
    word = data.get('word', '').strip()
    script = data.get('script', None)
    if not word:
        return jsonify({'error': 'word required'}), 400
    # Avtomatik aniqlash
    if not script:
        script = detect_script(word)
    if script == 'latin':
        checker = hunspell_latin
    else:
        checker = hunspell_cyrillic
    correct = checker.spell(word)
    suggestions = checker.suggest(word)
    return jsonify({
        'word': word,
        'script': script,
        'correct': correct,
        'suggestions': suggestions
    })

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=4000)
