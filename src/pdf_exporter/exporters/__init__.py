import anki.exporting
from anki.utils import pointVersion

# Anki 26 removed anki.exporting.Exporter, so the legacy exporter can only
# be loaded on Anki versions that still ship it.
LEGACY_EXPORTER_AVAILABLE = hasattr(anki.exporting, "Exporter")

if LEGACY_EXPORTER_AVAILABLE:
    from .legacy_exporter import initialize_exporters as initialize_legacy_exporters


def initialize_exporters():
    if LEGACY_EXPORTER_AVAILABLE:
        initialize_legacy_exporters()
    if pointVersion() >= 55:
        from .new_exporter import initialize_exporters as initialize_new_exporters

        initialize_new_exporters()
