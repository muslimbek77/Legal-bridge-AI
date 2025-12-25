import requests

# Lotin test
resp = requests.post('http://localhost:5005/api/spell', json={'word': 'xato'})
print('Lotin:', resp.json())

# Kirill test
resp = requests.post('http://localhost:5005/api/spell', json={'word': 'хатолик'})
print('Kirill:', resp.json())

# Avto-detect test
resp = requests.post('http://localhost:5005/api/spell', json={'word': 'kitob'})
print('Avto-detect:', resp.json())
