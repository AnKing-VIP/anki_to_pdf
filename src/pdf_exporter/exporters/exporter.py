from __future__ import annotations

import copy
import datetime
import re
from pathlib import Path
from shutil import copyfile
from typing import Sequence

from anki.cards import Card
from anki.collection import Collection
from anki.decks import DeckId
from anki.notes import Note, NoteId
from aqt import mw
from bs4 import BeautifulSoup  # type:ignore
from jinja2 import Environment, FileSystemLoader

from ..consts import (
    ADDON_PATH,
    DEFAULT_CSS_FILE_PATH,
    USER_CSS_FILE_PATH,
    USER_FILES_PATH,
)
from ..export_templates import get_export_styling, get_export_templates
from ..utils import open_link
from .common import export_options
from ..utils import read_text

jinja_env = Environment(loader=FileSystemLoader(ADDON_PATH))


class PDFExporter:
    def __init__(self) -> None:
        if not USER_CSS_FILE_PATH.exists():
            USER_FILES_PATH.mkdir(exist_ok=True, parents=True)
            copyfile(DEFAULT_CSS_FILE_PATH, USER_CSS_FILE_PATH)

        self.user_style = read_text(USER_CSS_FILE_PATH)

        media_uri = Path(mw.col.media.dir()).as_uri()
        self.base = f'<base href="{media_uri}/">'

    def index_css(self, card: Card, include_sched: bool):
        if not include_sched:
            return ""
        ease = card.factor / 10.0
        if ease < export_options["ease_threshold_lower"]:
            return "color:white; background-color:#F68787;"
        elif ease > export_options["ease_threshold_upper"]:
            return "color:white; background-color:#7CFF9E;"

    def escape_text(self, text):
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

    def do_export(
        self,
        col: Collection,
        path: str,
        did: DeckId | None,
        note_ids: Sequence[NoteId],
        include_sched: bool,
    ):
        deckname = (did and col.decks.name_if_exists(did)) or ""
        deckname = deckname.replace("::", " > ")

        cards = []
        for nidx, nid in enumerate(note_ids, 1):
            note: Note = col.get_note(nid)

            cards_for_note = []
            if export_templates := get_export_templates(note.note_type()["name"]):
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
                        "index_style": self.index_css(card, include_sched),
                        "question": self.escape_text(card.question()),
                        "answer": self.escape_text(card.answer()),
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
        with open(path, "w", encoding="utf-8") as file:
            file.write(html)
        open_link(path)
