"""
Fixed spelling checker implementation.
Replace the check_text method in /home/rasulbek/muslim-projects/Legal-bridge-AI/ai_engine/spelling/__init__.py
with this version.
"""

def check_text(self, text: str, language: str = 'uz-latn') -> List[SpellingError]:
    """
    Check text for spelling errors using heuristics and external backends.
    """
    # Check if we should use external-only mode
    spelling_mode = os.getenv('SPELLING_MODE', 'hybrid')
    if spelling_mode == 'matnuz-only':
        return self._check_external_only(text, language)
    
    # Full analysis with heuristics
    return self._check_text_full(text, language)
