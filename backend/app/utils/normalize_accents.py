import unicodedata

def strip_accents(text: str) -> str:
    """
    Décompose les caractères unicode (NFD), 
    filtre les marques diacritiques, puis recompose (NFC).
    """
    nfkd = unicodedata.normalize("NFD", text)
    without_diacritics = "".join(
        c for c in nfkd
        if unicodedata.category(c) != "Mn"
    )
    return unicodedata.normalize("NFC", without_diacritics)