ANKING_NOTETYPE_NAMES = [
    "AnKing",
    "AnKingDerm",
    "AnKingMCAT",
    "AnKingOverhaul",
    "Basic-AnKing",
    "Basic-AnKingLanguage",
    "IO-one by one",
    "Physeo-Cloze",
    "Physeo-IO one by one",
]


def anking_notetype_base_name(notetype_name: str) -> str:
    return next(
        (
            name
            for name in ANKING_NOTETYPE_NAMES
            if notetype_name == name or notetype_name.startswith(name + " ")
        ),
        None,
    )
