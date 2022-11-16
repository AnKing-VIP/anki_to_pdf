from anki.exporting import Exporter
from anki.hooks import exporters_list_created, wrap
from anki.utils import ids2str
from aqt import dialogs
from aqt.browser import Browser
from aqt.exporting import ExportDialog
from aqt.qt import *

from ..utils import unique
from .common import on_exporter_changed
from .exporter import PDFExporter


class AnkiToHtmlExporter(Exporter, PDFExporter):
    ext = ".html"
    includeSched = False

    def __init__(self, col):
        Exporter.__init__(self, col)
        PDFExporter.__init__(self)

    def _cardIdsByDeck(self, did, children=False):
        # adapted from anki.decks.cids
        if not children:
            return self.col.db.list(
                f"SELECT id FROM cards WHERE did={did} ORDER BY nid, ord"
            )
        dids = [did]
        for _, id in self.col.decks.children(did):
            dids.append(id)
        return self.col.db.list(
            f"SELECT id FROM cards WHERE did IN {ids2str(dids)} ORDER BY nid, ord"
        )

    def exportInto(self, path):
        self.do_export(self.col, path, self.did, self.noteIds(), self.includeSched)

    def cardIds(self):
        if self.cids is not None:
            cids = self.cids
        elif not self.did:
            cids = self.col.db.list("SELECT id FROM cards ORDER BY nid, ord")
        else:
            cids = self._cardIdsByDeck(self.did, children=True)
        self.count = len(cids)
        return cids

    def noteIds(self):

        # if selected notes are exported from the browser they should be exported in the same order
        # as they appear there
        browser: Browser = dialogs._dialogs["Browser"][1]
        if browser:
            selected_nids = []
            if (
                hasattr(
                    browser, "table"
                )  # browser.table doesn't exist in older anki versions
                and browser.table.is_notes_mode()
                and (nids := browser.selected_notes())
            ):
                selected_nids = nids
            elif (
                not hasattr(
                    browser, "table"
                )  # browser.table doesn't exist in older anki versions and there is no notes_mode
                or not browser.table.is_notes_mode()
            ) and (selected_cids := browser.selected_cards()):
                selected_nids = unique(
                    [self.col.get_card(cid).nid for cid in selected_cids]
                )

            if (
                selected_nids
                # the user could have some notes selected in the browser and
                # export other notes, in this case we don't want to change the exported nids
                and set(
                    self.col.db.list(
                        f"select id from cards where nid in {ids2str(selected_nids)}"
                    )
                )
                == set(self.cardIds())
            ):
                return selected_nids

        query = (
            "select id from notes "
            "where id in "
            f"(select nid from cards where cards.id in {ids2str(self.cardIds())}) "
            f"order by id"  # this effectively sorts the cards by created time
        )
        return [x for x in self.col.db.list(query) if x]


def initialize_exporters():
    def _add_exporters(exps):
        exps.append(
            (
                f"PDF Exporter (*{AnkiToHtmlExporter.ext})",
                AnkiToHtmlExporter,
            )
        )

    exporters_list_created.append(_add_exporters)
    ExportDialog.exporterChanged = wrap(
        ExportDialog.exporterChanged, on_exporter_changed, "after"
    )
