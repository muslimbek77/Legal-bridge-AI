"""
External spelling backends facade.
Backends are optional and only used if the corresponding dependency and
language dictionaries are available on the system.

Supported backends (optional):
- Enchant/Hunspell (via pyenchant) for Uzbek/Russian word-level checks
- LanguageTool (via language_tool_python) for Russian sentence-level checks
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BackendResult:
    correct: bool
    suggestion: Optional[str] = None


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
        self.backends = [EnchantBackend(), LanguageToolBackend()]

    def check(self, word: str, language: str) -> BackendResult:
        for backend in self.backends:
            res = backend.check(word, language)
            if not res.correct:
                return res
        return BackendResult(correct=True)
