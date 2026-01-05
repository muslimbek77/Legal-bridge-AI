import requests

def uzspell_check(word: str, api_url: str = "http://localhost:4000/api/spell") -> dict:
    """
    Uzspell API orqali so'zni tekshiradi.
    """
    try:
        resp = requests.post(api_url, json={"word": word}, timeout=3)
        if resp.status_code == 200:
            return resp.json()
        return {"correct": True, "suggestions": []}
    except Exception:
        return {"correct": True, "suggestions": []}
