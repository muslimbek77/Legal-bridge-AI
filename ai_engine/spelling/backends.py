"""
External spelling backends facade.
Backends are optional and only used if the corresponding dependency and
language dictionaries are available on the system.

Supported backends (optional):
- Matn.uz HTTP API for Uzbek spelling correction
- Yandex Speller for Russian
- Enchant/Hunspell (via pyenchant) for Uzbek/Russian word-level checks
- LanguageTool (via language_tool_python) for Russian sentence-level checks
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import requests

logger = logging.getLogger(__name__)


@dataclass
class BackendResult:
    """Result of a spelling check."""
    correct: bool
    suggestion: Optional[str] = None


class UzSpellBackend:
    """Local Flask uzspell API backend (lotin/kirill)."""
    API_URL = os.getenv("UZSPELL_API_URL", "http://localhost:4000/api/spell")
    TIMEOUT = 3.0

    def __init__(self):
        self._cache = {}

    def check(self, word: str, language: str) -> BackendResult:
        # Only check if language is Uzbek
        if not language.startswith('uz'):
            return BackendResult(correct=True)

        key = (word, language)
        if key in self._cache:
            return self._cache[key]
        try:
            resp = requests.post(self.API_URL, json={"word": word}, timeout=self.TIMEOUT)
            if resp.status_code != 200:
                return BackendResult(correct=True)
            data = resp.json()
            correct = data.get("correct", True)
            suggestions = data.get("suggestions", [])
            suggestion = None
            if not correct and suggestions:
                suggestion = suggestions[0]
            
            res = BackendResult(correct=correct, suggestion=suggestion)
            self._cache[key] = res
            return res
        except Exception:
            # Fail open (assume correct if backend down)
            return BackendResult(correct=True)


class YandexSpellerBackend:
    """Yandex.Speller API backend for Russian/English."""
    API_URL = "https://speller.yandex.net/services/spellservice.json/checkText"
    TIMEOUT = 5.0

    def __init__(self):
        self._cache = {}

    def check(self, word: str, language: str) -> BackendResult:
        # Yandex supports: ru, en, uk. Map 'rus' -> 'ru'
        lang_map = {'rus': 'ru', 'ru': 'ru', 'en': 'en', 'eng': 'en'}
        yandex_lang = lang_map.get(language)
        
        if not yandex_lang:
            return BackendResult(correct=True)

        key = (word, yandex_lang)
        if key in self._cache:
            return self._cache[key]

        try:
            # Yandex checkText takes a text block, but we check word by word here for consistency
            # Options: 512 (ignore digits) + 4 (ignore roman numerals)
            params = {
                'text': word,
                'lang': yandex_lang,
                'options': 516
            }
            resp = requests.post(self.API_URL, data=params, timeout=self.TIMEOUT)
            if resp.status_code != 200:
                return BackendResult(correct=True)
            
            data = resp.json()
            # data is a list of errors. If empty, word is correct.
            if not data:
                res = BackendResult(correct=True)
            else:
                # Take the first error's first suggestion
                error = data[0]
                suggs = error.get('s', [])
                suggestion = suggs[0] if suggs else None
                res = BackendResult(correct=False, suggestion=suggestion)
            
            self._cache[key] = res
            return res
        except Exception:
            return BackendResult(correct=True)


class MatnUzBackend:
    """Matn.uz API client."""
    API_URL = "https://matn.uz/api/v1/correct"

    def __init__(self, token: Optional[str] = None, timeout: float = 4.0) -> None:
        self._token = token or os.getenv("MATNUZ_API_TOKEN") or os.getenv("MATN_UZ_API_TOKEN")
        self._timeout = timeout
        self._cache: Dict[tuple[str, str], BackendResult] = {}
        try:
            self._session = requests.Session()
        except Exception:
            self._session = None

    @property
    def available(self) -> bool:
        return bool(self._token and self._session)

    def check(self, word: str, language: str) -> BackendResult:
        if not self.available:
            return BackendResult(correct=True)
        
        # Only for Uzbek
        if not language.startswith('uz'):
            return BackendResult(correct=True)

        key = (language, word)
        if key in self._cache:
            return self._cache[key]

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        payload = {"text": word, "lang": "uz"}

        try:
            response = self._session.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
            if response.status_code >= 500:
                return BackendResult(correct=True)

            # Simplified parsing logic
            data = response.json()
            suggestion = None
            if isinstance(data, dict):
                if data.get('corrected_text') and data['corrected_text'] != word:
                    suggestion = data['corrected_text']
            
            result = BackendResult(correct=(suggestion is None), suggestion=suggestion)
            self._cache[key] = result
            return result
        except Exception:
            return BackendResult(correct=True)


class EnchantBackend:
    """Thin wrapper around pyenchant dictionaries."""
    def __init__(self) -> None:
        try:
            import enchant
            self._enchant = enchant
            self._available = True
        except ImportError:
            self._available = False
        self._dicts = {}

    def check(self, word: str, language: str) -> BackendResult:
        if not self._available:
            return BackendResult(correct=True)
        
        # Map language
        tag = None
        if language == 'ru': tag = 'ru_RU'
        elif language == 'uz-latn': tag = 'uz_UZ'
        # uz-cyrl is not supported by standard enchant dictionaries usually, unless installed
        
        if not tag:
             return BackendResult(correct=True)
        
        if tag not in self._dicts:
            try:
                self._dicts[tag] = self._enchant.Dict(tag)
            except Exception:
                self._dicts[tag] = None
        
        d = self._dicts[tag]
        if not d:
            return BackendResult(correct=True)
            
        if d.check(word):
            return BackendResult(correct=True)
        
        sugg = d.suggest(word)
        return BackendResult(correct=False, suggestion=sugg[0] if sugg else None)


class CombinedBackend:
    """Try multiple backends in order until one yields a correction."""

    def __init__(self) -> None:
        # Order matters: Local/Specific -> General
        self.backends = [
            UzSpellBackend(),
            YandexSpellerBackend(),
            MatnUzBackend(),
            EnchantBackend()
        ]

    def check(self, word: str, language: str) -> BackendResult:
        for backend in self.backends:
            res = backend.check(word, language)
            if not res.correct:
                return res
        return BackendResult(correct=True)
