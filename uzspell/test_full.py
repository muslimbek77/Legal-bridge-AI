import requests

# Matn test (lotin, kirill, ruscha)
matnlar = [
    "xato xamda xech kim yo'q", # lotin
    "хатолик ва хеч ким йўқ",    # kirill
    "Превет мир ошибка"          # ruscha
]

for matn in matnlar:
    print(f"\nMatn: {matn}")
    for word in matn.split():
        # Uzspell API
        uzspell = requests.post('http://localhost:4000/api/spell', json={'word': word})
        print(f"  Uzspell: {word} -> {uzspell.json()}")
        # Yandex Speller (ruscha)
        yandex = requests.get('https://speller.yandex.net/services/spellservice.json/checkText', params={'text': word})
        print(f"  Yandex: {word} -> {yandex.json()}")
