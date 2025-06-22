from anki.utils import pointVersion

from .legacy_exporter import initialize_exporters as initialize_legacy_exporters


def initialize_exporters():
    initialize_legacy_exporters()
    if pointVersion() >= 55:
        from .new_exporter import initialize_exporters as initialize_new_exporters

        initialize_new_exporters()
