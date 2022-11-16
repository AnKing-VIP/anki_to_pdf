from aqt import appVersion

from .legacy_exporter import initialize_exporters as initialize_legacy_exporters

anki_version = tuple(int(p) for p in appVersion.split("."))


def initialize_exporters():
    initialize_legacy_exporters()
    if anki_version >= (2, 1, 55):
        from .new_exporter import initialize_exporters as initialize_new_exporters

        initialize_new_exporters()
