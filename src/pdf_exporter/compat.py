import copy

import anki
from anki.cards import Card
from anki.collection import Collection
from anki.notes import Note
from anki.template import TemplateRenderContext
from aqt import mw
from aqt.browser import Browser
from aqt.gui_hooks import profile_did_open


def add_compat_aliases():
    add_compat_alias(Note, "note_type", "model")
    add_compat_alias(anki.utils, "is_win", "isWin")
    add_compat_alias(anki.utils, "is_mac", "isMac")
    add_compat_method(Note, "ephemeral_card", ephemeral_card)
    add_compat_method(Browser, "selected_notes", "selectedNotes")
    add_compat_method(Browser, "selected_cards", "selectedCards")
    add_compat_method(Collection, "get_card", "getCard")

    try:
        from aqt.browser import Table

        add_compat_method(Table, "is_notes_mode", lambda self: False)
    except:
        pass

    profile_did_open.append(lambda: add_compat_alias(mw.col, "get_note", "getNote"))
    profile_did_open.append(
        lambda: add_compat_alias(mw.col.decks, "name_if_exists", "nameOrNone")
    )


def add_compat_alias(namespace, new_name, old_name):
    if new_name not in dir(namespace):
        setattr(namespace, new_name, getattr(namespace, old_name))
        return True

    return False


def add_compat_method(namespace, name, function):
    if name not in dir(namespace):
        setattr(namespace, name, function)
        return True

    return False


def ephemeral_card(self: Note, custom_note_type, ord) -> Card:
    # adapted from ephemeral_card_for_rendering(self) from clayout.py in Anki 2.1.40
    card = Card(mw.col)
    card.ord = ord
    card.did = 1  # type: ignore
    template = copy.copy(custom_note_type["tmpls"][ord])
    # may differ in cloze case
    template["ord"] = card.ord
    output = TemplateRenderContext.from_card_layout(
        self,
        card,
        notetype=self.model(),
        template=template,
        fill_empty=False,
    ).render()
    card.set_render_output(output)
    card._note = self
    return card
