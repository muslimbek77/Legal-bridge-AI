"""
External spelling backends facade.
Backends are optional and only used if the corresponding dependency and
language dictionaries are available on the system.

Supported backends (optional):
- Matn.uz HTTP API for Uzbek spelling correction
- Enchant/Hunspell (via pyenchant) for Uzbek/Russian word-level checks
- LanguageTool (via language_tool_python) for Russian sentence-level checks
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
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
            result = BackendResult(correct=correct, suggestion=suggestion)
        except Exception:
            result = BackendResult(correct=True)
        self._cache[key] = result
        return result
"""
External spelling backends facade.
Backends are optional and only used if the corresponding dependency and
language dictionaries are available on the system.

Supported backends (optional):
- Matn.uz HTTP API for Uzbek spelling correction
- Enchant/Hunspell (via pyenchant) for Uzbek/Russian word-level checks
- LanguageTool (via language_tool_python) for Russian sentence-level checks
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _safe_lower(value: Optional[str]) -> str:
    """Lower-case helper that tolerates None."""
    return value.lower() if isinstance(value, str) else ""


@dataclass
class BackendResult:
    correct: bool
    suggestion: Optional[str] = None


class MatnUzBackend:
    """Matn.uz API client.

    Uses the /api/v1/correct endpoint to obtain spelling suggestions. The
    backend is intentionally tolerant: missing dependencies, missing tokens or
    transient HTTP failures will simply skip correction instead of failing the
    pipeline.
    """

    API_URL = "https://matn.uz/api/v1/correct"

    def __init__(self, token: Optional[str] = None, timeout: float = 4.0) -> None:
        self._token = token or os.getenv("MATNUZ_API_TOKEN") or os.getenv("MATN_UZ_API_TOKEN")
        self._timeout = timeout
        self._cache: Dict[tuple[str, str], BackendResult] = {}

        try:
            import requests  # type: ignore

            self._requests = requests
            self._session = requests.Session()
        except Exception:
            self._requests = None
            self._session = None

    @property
    def available(self) -> bool:
        return bool(self._token and self._session and self._requests)

    def _normalize_lang(self, language: str) -> str:
        if not language:
            return "uz"
        # Matn.uz primarily supports Uzbek; fall back to uz for other variants
        if language.startswith("uz"):
            return "uz"
        return language

    def check(self, word: str, language: str) -> BackendResult:
        if not self.available:
            return BackendResult(correct=True)

        lang = self._normalize_lang(language)
        cache_key = (lang, word)
        if cache_key in self._cache:
            return self._cache[cache_key]

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        payload = {"text": word, "lang": lang}

        try:
            response = self._session.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
            if response.status_code >= 500:
                return BackendResult(correct=True)

            suggestion = self._parse_response(response.json(), word)
            result = BackendResult(correct=(suggestion is None), suggestion=suggestion)
        except Exception as exc:  # Network or JSON errors
            logger.debug("Matn.uz backend failed; skipping: %s", exc)
            result = BackendResult(correct=True)

        self._cache[cache_key] = result
        return result

    def _parse_response(self, data: Any, original: str) -> Optional[str]:
        """Extract a suggestion from a Matn.uz response.

        The API shape is not strictly documented; this method accepts several
        possible layouts without failing the pipeline.
        """

        def pick_from_container(container: Dict[str, Any]) -> Optional[str]:
            if not isinstance(container, dict):
                return None

            # Direct corrected text fields
            for key in ("corrected_text", "correctedText", "result", "correct_text"):
                val = container.get(key)
                sugg = normalize_value(val)
                if sugg:
                    return sugg

            # Arrays of corrections/errors/suggestions
            for key in ("corrections", "errors", "result", "suggestions"):
                val = container.get(key)
                sugg = normalize_value(val)
                if sugg:
                    return sugg

            # Boolean flags with suggestion fields
            if container.get("correct") is False or container.get("is_correct") is False:
                sugg = normalize_value(
                    container.get("suggestion")
                    or container.get("suggest")
                    or container.get("expected")
                )
                if sugg:
                    return sugg

            return None

        def normalize_value(value: Any) -> Optional[str]:
            """Handle strings, dicts, or lists and return a suggestion."""
            if isinstance(value, str):
                value = value.strip()
                if value and _safe_lower(value) != _safe_lower(original):
                    return value
                return None

            if isinstance(value, dict):
                for key in ("suggestion", "suggest", "expected", "replace", "replace_to", "correct"):
                    cand = value.get(key)
                    normalized = normalize_value(cand)
                    if normalized:
                        return normalized
                return None

            if isinstance(value, list):
                for item in value:
                    normalized = normalize_value(item)
                    if normalized:
                        return normalized
                return None

            return None

        # If the API returns a plain string
        if isinstance(data, str):
            data = data.strip()
            if data and _safe_lower(data) != _safe_lower(original):
                return data
            return None

        # If the API nests payload under a data key
        if isinstance(data, dict):
            suggestion = pick_from_container(data)
            if suggestion:
                return suggestion
            nested = data.get("data")
            if nested:
                return pick_from_container(nested)

        return None


class YandexSpellerBackend:
    """Yandex Speller API for Russian text."""

    API_URL = "https://speller.yandex.net/services/spellservice.json/checkText"

    def __init__(self, timeout: float = 4.0) -> None:
        self._timeout = timeout
        self._cache: Dict[tuple[str, str], BackendResult] = {}
        try:
            import requests  # type: ignore

            self._requests = requests
            self._session = requests.Session()
        except Exception:
            self._requests = None
            self._session = None

    @property
    def available(self) -> bool:
        return bool(self._session and self._requests)

    def check(self, word: str, language: str) -> BackendResult:
        if language != "ru":
            return BackendResult(correct=True)
        if not self.available:
            return BackendResult(correct=True)

        cache_key = (language, word)
        if cache_key in self._cache:
            return self._cache[cache_key]

        params = {"text": word, "lang": "ru"}
        try:
            resp = self._session.get(self.API_URL, params=params, timeout=self._timeout)
            if resp.status_code >= 500:
                result = BackendResult(correct=True)
            else:
                data = resp.json()
                suggestion = self._parse_response(data, word)
                result = BackendResult(correct=(suggestion is None), suggestion=suggestion)
        except Exception as exc:
            logger.debug("Yandex Speller backend failed; skipping: %s", exc)
            result = BackendResult(correct=True)

        self._cache[cache_key] = result
        return result

    def _parse_response(self, data: Any, original: str) -> Optional[str]:
        """Extract first suggestion from Yandex Speller response."""
        if not isinstance(data, list):
            return None
        for item in data:
            if not isinstance(item, dict):
                continue
            suggestions = item.get("s")
            if suggestions and isinstance(suggestions, list):
                for s in suggestions:
                    if isinstance(s, str) and _safe_lower(s) != _safe_lower(original):
                        return s
        return None


class EnchantBackend:
    """Thin wrapper around pyenchant dictionaries.

    This backend checks single words. It requires system hunspell dictionaries
    (e.g., uz_UZ, uz_UZ@cyrillic, ru_RU) to be installed and accessible by
    Enchant.
    """

    def __init__(self) -> None:
        try:
            import enchant  # type: ignore
        except Exception:
            self._available = False
            self._enchant = None
            self._dicts = {}
            return

        self._available = True
        self._enchant = enchant
        self._dicts = {}

    def _get_dict_tag(self, language: str) -> list[str]:
        # Map our language codes to possible enchant dict tags
        if language == 'uz-latn':
            # Many distros provide one of these for Uzbek
            return ['uz_UZ', 'uz_UZ-latn', 'uz']
        if language == 'uz-cyrl':
            return ['uz_UZ@cyrillic', 'uz_UZ', 'uz']
        if language == 'ru':
            return ['ru_RU', 'ru']
        return []

    def _load_dict(self, language: str):
        if not self._available:
            return None
        if language in self._dicts:
            return self._dicts[language]

        tags = self._get_dict_tag(language)
        for tag in tags:
            try:
                if self._enchant.Dict(tag):
                    d = self._enchant.Dict(tag)
                    self._dicts[language] = d
                    return d
            except Exception:
                continue
        # Cache negative result to avoid repeated lookups
        self._dicts[language] = None
        return None

    def check(self, word: str, language: str) -> BackendResult:
        d = self._load_dict(language)
        if not d:
            return BackendResult(correct=True)
        try:
            if d.check(word):
                return BackendResult(correct=True)
            # Suggest only the top suggestion, if any
            sugg = d.suggest(word)
            return BackendResult(correct=False, suggestion=(sugg[0] if sugg else None))
        except Exception:
            # On any backend error, do not flag the word
            return BackendResult(correct=True)


class LanguageToolBackend:
    """Wrapper for LanguageTool (useful for Russian).

    LanguageTool works best on sentences. For single-word checks we pass the
    token as a sentence; if any spelling rule flags it with a suggestion,
    we surface the top suggestion.
    """

    def __init__(self) -> None:
        try:
            import language_tool_python  # type: ignore
        except Exception:
            self._available = False
            self._tool = None
            return

        self._available = True
        self._tool = None
        self._lt_module = language_tool_python

    def _ensure_tool(self, language: str):
        if not self._available:
            return None
        if self._tool is not None:
            return self._tool
        # Only initialize for Russian; Uzbek is not supported in LT
        if language == 'ru':
            try:
                self._tool = self._lt_module.LanguageTool('ru-RU')
                return self._tool
            except Exception:
                self._tool = None
                return None
        return None

    def check(self, word: str, language: str) -> BackendResult:
        tool = self._ensure_tool(language)
        if not tool:
            return BackendResult(correct=True)
        try:
            matches = tool.check(word)
            if not matches:
                return BackendResult(correct=True)
            # Find a spelling-related match with suggestions
            for m in matches:
                if getattr(m, 'replacements', None):
                    # Return first suggestion
                    return BackendResult(correct=False, suggestion=m.replacements[0])
            return BackendResult(correct=False, suggestion=None)
        except Exception:
            return BackendResult(correct=True)


class CombinedBackend:
    """Try multiple backends in order until one yields a correction."""

    def __init__(self) -> None:
        self.backends = [UzSpellBackend(), MatnUzBackend(), YandexSpellerBackend(), EnchantBackend(), LanguageToolBackend()]

    def check(self, word: str, language: str) -> BackendResult:
        for backend in self.backends:
            res = backend.check(word, language)
            if not res.correct:
                return res
        return BackendResult(correct=True)
