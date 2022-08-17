from copy import deepcopy
from typing import Any, Dict, List

from aqt import mw
from aqt.clayout import CardLayout
from aqt.qt import *
from aqt.utils import tooltip

try:
    from aqt.utils import disable_help_button  # not available in < 2.1.40
except:
    pass

from .export_templates import (create_templates_dir_if_not_exists,
                               existing_export_template_ords,
                               get_export_styling, get_export_styling_path,
                               get_export_template_paths)
from .utils import open_file

# used to restore original templates to make it easier for the user to create modified versions of them
original_templates = None
original_styling = None

# saving these Qt objects here so they don't get garbage collected
menu = None
saveAct = None
manageAct = None
loadAct = None
removeAct = None
saveStylingAct = None


def add_export_template_managment_to_clayout(clayout: CardLayout):
    button = QPushButton()
    button.setAutoDefault(False)
    button.setText("PDF Exporter templates")

    global menu, saveAct, manageAct, loadAct, removeAct, saveStylingAct, original_templates, original_styling
    original_templates = deepcopy(clayout.templates)
    original_styling = clayout.model["css"]
    menu = QMenu()

    saveAct = QAction("Save current template")
    saveAct.triggered.connect(  # type: ignore
        lambda: _save_current_template_as_export_template(clayout)
    )
    menu.addAction(saveAct)

    loadAct = QAction("Load template")
    loadAct.triggered.connect(lambda: _load_export_tempplate_into_clayout(clayout) or disable_save_button(clayout))  # type: ignore
    menu.addAction(loadAct)

    removeAct = QAction("Remove template")
    removeAct.triggered.connect(lambda: _remove_export_template(clayout))  # type: ignore
    menu.addAction(removeAct)

    saveStylingAct = QAction("Save styling")
    saveStylingAct.triggered.connect(lambda: _save_export_styling(clayout))  # type: ignore
    menu.addAction(saveStylingAct)

    manageAct = QAction("Open templates and styling in file explorer")
    manageAct.triggered.connect(lambda: _manage_export_templates(clayout))  # type: ignore
    menu.addAction(manageAct)

    button.setMenu(menu)

    button.clicked.connect(lambda: _save_current_template_as_export_template(clayout) or disable_save_button(clayout))  # type: ignore
    clayout.buttons.insertWidget(1, button)


def disable_save_button(clayout: CardLayout):
    for idx in range(clayout.buttons.count()):
        widget = clayout.buttons.itemAt(idx).widget()
        if not isinstance(widget, QPushButton) or widget.text() != "Save":
            continue
        widget.setDisabled(True)
        widget.setToolTip("Saving is disabled AnkiToPdf template was edited")


def _save_current_template_as_export_template(clayout: CardLayout):
    template = clayout.current_template()

    ords = (existing := existing_export_template_ords(clayout.model["name"])) + [
        _smallest_available_ord(existing)
    ]
    choice_idx = let_user_choose_from_list(
        "Choose template to save this to", list(map(str, ords))
    )
    if choice_idx is None:
        return
    ord = ords[choice_idx]
    get_export_template_paths(clayout.model["name"], ord)[0].write_text(
        template["qfmt"]
    )
    get_export_template_paths(clayout.model["name"], ord)[1].write_text(
        template["afmt"]
    )


def _manage_export_templates(clayout: CardLayout):
    templates_dir = create_templates_dir_if_not_exists(clayout.model["name"])
    open_file(templates_dir)


def _load_export_tempplate_into_clayout(clayout: CardLayout):
    choices = ["original"] + list(
        map(str, existing_export_template_ords(clayout.model["name"]))
    )

    template = None
    choice_idx = let_user_choose_from_list(
        "Choose template to save this to", list(map(str, choices))
    )
    if choice_idx is None:
        return
    choice = choices[choice_idx]
    if choice == "original":
        template = deepcopy(original_templates[clayout.ord])
        clayout.model["css"] = original_styling
    else:
        ord = int(choice)
        template = {
            "name": clayout.current_template()["name"],
            "qfmt": get_export_template_paths(clayout.model["name"], ord)[
                0
            ].read_text(),
            "afmt": get_export_template_paths(clayout.model["name"], ord)[
                1
            ].read_text(),
            "ord": clayout.current_template()["ord"],
        }
        clayout.model["css"] = get_export_styling(clayout.model["name"])
    _load_template_into_clayout(clayout, template)


def _load_template_into_clayout(clayout: CardLayout, template: Dict):
    scroll_bar = clayout.tform.edit_area.verticalScrollBar()
    scroll_pos = scroll_bar.value()
    clayout.templates[clayout.ord] = template
    clayout.change_tracker.mark_basic()
    clayout.update_current_ordinal_and_redraw(clayout.ord)

    # not sure why but this is needed with AnKingOverhaul template because
    # display of qa is set to none when loading the export template from the original front template
    clayout.preview_web.eval(
        "document.getElementById('qa').style.removeProperty('display')"
    )

    scroll_bar.setValue(min(scroll_pos, scroll_bar.maximum()))


def _remove_export_template(clayout: CardLayout):
    ords = existing_export_template_ords(clayout.model["name"])
    if not ords:
        tooltip("No templates to remove")
        return

    choice_idx = let_user_choose_from_list(
        "Choose export template to remove", list(map(str, ords))
    )
    if choice_idx is None:
        return
    ord = ords[choice_idx]
    get_export_template_paths(clayout.model["name"], ord)[0].unlink()
    get_export_template_paths(clayout.model["name"], ord)[1].unlink()


def _smallest_available_ord(ords: List[int]) -> int:
    # export template ords start at 1, unlike other ords in Anki
    ords_set = set(ords)
    for i in range(1, len(ords_set) + 2):
        if i not in ords_set:
            return i
    assert False


def _save_export_styling(clayout: CardLayout):
    get_export_styling_path(clayout.model["name"]).write_text(clayout.model["css"])


def let_user_choose_from_list(
    prompt: str, choices: list[str], startrow: int = 0, parent: Any = None
) -> int:
    # adapted from aqt.utils chooseList
    # returns None when dialog is rejected

    if not parent:
        parent = mw.app.activeWindow()
    d = QDialog(parent)

    try:
        disable_help_button(d)
    except:
        pass

    d.setWindowModality(Qt.WindowModality.WindowModal)
    l = QVBoxLayout()
    d.setLayout(l)
    t = QLabel(prompt)
    l.addWidget(t)
    c = QListWidget()
    c.addItems(choices)
    c.setCurrentRow(startrow)
    l.addWidget(c)
    bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
    qconnect(bb.accepted, d.accept)
    l.addWidget(bb)
    if d.exec():
        return c.currentRow()
    else:
        return None
