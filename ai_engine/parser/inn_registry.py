# Optional local INN→organization name fallback mapping.
# Extend this mapping with known INNs in your dataset.

KNOWN_INN_NAMES = {
    '200640852': "KO'PRIKQURILISH AJ",
    '305127905': 'SIFAT SITY STROY SSS',
    '303426835': 'SHAXRUZA SHOXRUX VERSAL HAMKOR MChJ',
    '200796358': "Қўприкқурилиш АЖ",
}

def resolve_inn_name(inn: str) -> str | None:
    return KNOWN_INN_NAMES.get(inn)
