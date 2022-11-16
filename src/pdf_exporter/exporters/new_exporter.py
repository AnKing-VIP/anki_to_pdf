from typing import Type

from anki.collection import CardIdsLimit, DeckIdLimit, NoteIdsLimit, SearchNode
from anki.hooks import wrap
from aqt.gui_hooks import exporters_list_did_initialize
from aqt.import_export.exporting import ExportDialog, Exporter, ExportOptions
from aqt.main import AnkiQt
from aqt.qt import *

from ..utils import unique
from .common import on_exporter_changed
from .exporter import PDFExporter


class AnkiToHtmlExporter(Exporter, PDFExporter):
    extension = "html"
    show_deck_list = True
    show_include_scheduling = True

    def export(self, mw: AnkiQt, options: ExportOptions) -> None:
        did = None
        if isinstance(options.limit, DeckIdLimit):
            did = options.limit.deck_id
            deck_name = mw.col.decks.name_if_exists(did) or ""
            note_ids = mw.col.find_notes(
                mw.col.build_search_string(SearchNode(deck=deck_name))
            )
        elif isinstance(options.limit, NoteIdsLimit):
            note_ids = options.limit.note_ids
        elif isinstance(options.limit, CardIdsLimit):
            note_ids = unique(
                mw.col.get_card(cid).nid for cid in options.limit.card_ids
            )
        else:
            note_ids = mw.col.find_notes("deck:*")

        self.do_export(
            mw.col, options.out_path, did, note_ids, options.include_scheduling
        )

    @staticmethod
    def name() -> str:
        return "PDF Exporter"


def initialize_exporters():
    def _add_exporters(exps: list[Type[Exporter]]):
        exps.append(AnkiToHtmlExporter)

    ExportDialog.exporter_changed = wrap(
        ExportDialog.exporter_changed, on_exporter_changed, "after"
    )
    exporters_list_did_initialize.append(_add_exporters)
