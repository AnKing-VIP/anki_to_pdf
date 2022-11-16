from typing import TYPE_CHECKING

from aqt.qt import *

if TYPE_CHECKING:
    from aqt.import_export.exporting import ExportDialog

from ..consts import USER_CSS_FILE_PATH
from ..utils import open_file

export_options = {
    "column_count": 1,
    "font_size": 9,
    "question_col_width": 18,
    "max_img_width": 35,
    "max_img_height": 35,
    "ease_threshold_lower": 210,
    "ease_threshold_upper": 260,
}


def on_exporter_changed(self: "ExportDialog", idx):
    from .exporter import PDFExporter

    if not isinstance(self.exporter, PDFExporter):
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
