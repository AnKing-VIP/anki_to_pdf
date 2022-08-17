from shutil import copytree, rmtree

from aqt.gui_hooks import card_layout_will_show
from aqt.qt import *

from .clayout import add_export_template_managment_to_clayout
from .compat import add_compat_aliases
from .consts import ANKING_EXPORT_TEMPLATES_PATH, USER_FILES_PATH
from .exporter import initialize_exporters
from .gui.anking_menu import get_anking_menu  # type: ignore

USER_FILES_PATH.mkdir(exist_ok=True)

add_compat_aliases()

initialize_exporters()

card_layout_will_show.append(add_export_template_managment_to_clayout)


def reset_anking_export_templates():
    for folder in ANKING_EXPORT_TEMPLATES_PATH.iterdir():
        if not folder.is_dir():
            continue

        rmtree(USER_FILES_PATH / folder.name, ignore_errors=True)
        copytree(
            ANKING_EXPORT_TEMPLATES_PATH / folder.name, USER_FILES_PATH / folder.name
        )


def setup_menu() -> None:
    anking_menu = get_anking_menu()
    pdf_exporter_menu = QMenu("PDF Exporter", anking_menu)
    anking_menu.addMenu(pdf_exporter_menu)

    reset_anking_export_templates_action = QAction(
        "Reset AnKing Export templates", pdf_exporter_menu
    )
    reset_anking_export_templates_action.triggered.connect(reset_anking_export_templates)  # type: ignore
    pdf_exporter_menu.addAction(reset_anking_export_templates_action)


setup_menu()
