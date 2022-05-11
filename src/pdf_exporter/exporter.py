import copy
import datetime
import re
from pathlib import Path
from shutil import copyfile

from anki.exporting import Exporter
from anki.hooks import exporters_list_created, wrap
from anki.notes import Note
from anki.utils import ids2str
from aqt import mw
from aqt.exporting import ExportDialog
from aqt.qt import *
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

from .export_templates import get_export_styling
from .utils import open_file, open_link

ADDON_PATH = Path(__file__).parent
USERFILES_PATH = ADDON_PATH / "user_files"
USER_CSS_FILE_PATH = USERFILES_PATH / "user.css"
DEFAULT_CSS_FILE_PATH = Path(ADDON_PATH) / "default.css"

jinja_env = Environment(loader=FileSystemLoader(ADDON_PATH))

export_options = {
    "column_count": 1,
    "font_size": 9,
    "question_col_width": 18,
    "max_img_width": 35,
    "max_img_height": 35,
    "ease_threshold_lower": 210,
    "ease_threshold_upper": 260,
}


class AnkiToHtmlExporter(Exporter):
    ext = ".html"
    includeSched = False

    def __init__(self, col):
        Exporter.__init__(self, col)

        if not USER_CSS_FILE_PATH.exists():
            copyfile(DEFAULT_CSS_FILE_PATH, USER_CSS_FILE_PATH)

        self.user_style = USER_CSS_FILE_PATH.read_text()

        media_uri = Path(mw.col.media.dir()).as_uri()
        self.base = f'<base href="{media_uri}/">'

    def escapeText(self, text):
        # Strip off the repeated question in answer if exists
        text = re.sub("(?si)^.*<hr id=answer>\n*", "", text)
        text = re.sub("(?si)<style.*?>.*?</style>", "", text)

        # Escape newlines, tabs and CSS.
        text = text.replace("\n", "")
        text = text.replace("\t", "")
        text = re.sub("(?i)<style>.*?</style>", "", text)

        # extra <br>s
        text = re.sub("(<br>|<br />|<br/>){3,}", "<br /><br />", text)

        # empty divs, etc.
        soup = BeautifulSoup(text, features="html.parser")
        for x in soup.findAll():
            # don't remove if elm contains singleton tag we want to keep
            if (
                x.name not in ("br", "hr", "img")
                and not x.findAll(("img", "hr"), recursive=True)
                and not x.text
            ):
                x.extract()

        text = str(soup)
        return text

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

    def indexCss(self, card):
        if not self.includeSched:
            return ""

        ease = card.factor / 10.0
        if ease < export_options["ease_threshold_lower"]:
            return "color:white; background-color:#F68787;"
        elif ease > export_options["ease_threshold_upper"]:
            return "color:white; background-color:#7CFF9E;"

    def doExport(self, file):
        deckname = self.col.decks.name_if_exists(self.did) or ""
        deckname = deckname.replace("::", " > ")

        cards = []
        for nidx, nid in enumerate(self.noteIds(), 1):
            note: Note = self.col.get_note(nid)

            cards_for_note = []
            if export_templates := export_templates(note.note_type()["name"]):
                model = copy.deepcopy(note.note_type())
                model.update(
                    {
                        "tmpls": export_templates,
                        "css": get_export_styling(note.note_type()["name"]),
                    }
                )
                cards_for_note = [
                    note.ephemeral_card(
                        custom_note_type=model,
                        ord=ord,
                    )
                    for ord in range(len(export_templates))
                ]
            else:
                cards_for_note = note.cards()

            for cidx, card in enumerate(cards_for_note, 1):
                cards.append(
                    {
                        "index": f"{nidx}.{cidx}",
                        "index_style": self.indexCss(card),
                        "question": self.escapeText(card.question()),
                        "answer": self.escapeText(card.answer()),
                    }
                )

        context = {
            "cur": {
                "deck_name": deckname,
                "num_cards": len(cards),
                "date": datetime.datetime.today().strftime("%Y-%m-%d"),
            },
            "cards": cards,
            "exporter": self.__dict__,
            "export_options": export_options,
        }

        template = jinja_env.get_template("table.html.j2")
        html = template.render(**context)
        file.write(html.encode("utf8"))

    def exportInto(self, path):
        super().exportInto(path)
        open_link(path)

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
        return [
            x[0]
            for x in self.col.db.execute(
                f"""
select id from notes
where id in
(select nid from cards
where cards.id in {ids2str(self.cardIds())})
order by guid"""
            )
            if x
        ]


def on_exporter_changed(self: ExportDialog, idx):
    if not isinstance(self.exporter, AnkiToHtmlExporter):
        if hasattr(self.frm, "export_options_container"):
            self.frm.export_options_container.setVisible(False)  # type: ignore
        return

    self.frm.includeSched.setChecked(False)

    if hasattr(self.frm, "export_options_container"):
        self.frm.export_options_container.setVisible(True)  # type: ignore
    else:
        setup_anki_to_pdf_options(self.frm)


def setup_anki_to_pdf_options(form):
    form.export_options_container = QWidget()
    layout = QVBoxLayout()
    form.export_options_container.setLayout(layout)
    form.vboxlayout.insertWidget(3, form.export_options_container)

    def add_input(key, label, min=None, max=None):
        input = QSpinBox()
        input.setMaximumWidth(60)

        if min is not None:
            input.setMinimum(min)
        if max is not None:
            input.setMaximum(max)

        input.setValue(export_options[key])

        input.valueChanged.connect(
            lambda: export_options.__setitem__(key, input.value())
        )

        container = QWidget()
        group_layout = QHBoxLayout()
        container.setLayout(group_layout)

        group_layout.addWidget(input)

        label = QLabel(label)
        group_layout.addWidget(label)

        layout.addWidget(container)

    text_about_pdf = QLabel(
        '<i>You can create a pdf by using the "print to pdf" feature<br>of your browser after exporting as html.</i>'
    )
    layout.addWidget(text_about_pdf)

    add_input("column_count", "columns", min=0, max=3)
    add_input("font_size", "font size")
    add_input("question_col_width", "width of the question column in %")
    add_input("max_img_width", "maximum image width %")
    add_input("max_img_height", "maximum image height %")

    open_styling_file_btn = QPushButton("Edit global styling file")
    open_styling_file_btn.setSizePolicy(
        QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
    )
    open_styling_file_btn.setAutoDefault(False)
    open_styling_file_btn.clicked.connect(lambda: open_file(USER_CSS_FILE_PATH))
    layout.addWidget(open_styling_file_btn)

    layout.addSpacing(10)

    layout.addWidget(
        QLabel("Options below only work when exporting\nwith scheduling information:")
    )
    add_input(
        "ease_threshold_lower",
        "cards with ease < x will be marked red",
        min=0,
        max=1000,
    )
    add_input(
        "ease_threshold_upper",
        "cards with ease > x will be marked green",
        min=0,
        max=1000,
    )

    layout.addStretch(0)


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
