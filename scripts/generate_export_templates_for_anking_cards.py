import json
import shutil
from pathlib import Path

NOTE_TYPES_PATH = Path(__file__).parent / "note_types"
OUT_PATH = Path(__file__).parent.parent / "src/pdf_exporter/anking_export_templates"

FIELDS_TO_IGNORE = ["OME", "One by one"]
FIELDS_TO_KEEP_ON_BACK_OF_CLOZE = ["Extra"]

for directory in NOTE_TYPES_PATH.iterdir():
    with open(str(next(directory.glob("*.json"), "r"))) as f:
        note_type_dict = json.load(f)

    front_html = ""
    back_html = ""
    for ord, field in enumerate(note_type_dict["flds"]):
        if field["name"] in FIELDS_TO_IGNORE:
            continue

        if ord == 0:
            if note_type_dict["type"] == 1:
                back_html += f"{{{{cloze:{field['name']}}}}}<br>\n"
            else:
                back_html += f"{{{{{field['name']}}}}}<br>\n"
            front_html = back_html
            continue

        line = f"{{{{#{field['name']}}}}}{{{{{field['name']}}}}}{{{{/{field['name']}}}}}<br>"
        if (
            note_type_dict["type"] == 1
            and field["name"] not in FIELDS_TO_KEEP_ON_BACK_OF_CLOZE
        ):
            line = f"<!-- {line} -->"
        back_html += f"{line}\n"

    out_directory = OUT_PATH / directory.name
    if out_directory.exists():
        shutil.rmtree(out_directory)
    out_directory.mkdir()

    (out_directory / "card1_front.html").write_text(front_html, encoding="utf-8")
    (out_directory / "card1_back.html").write_text(back_html, encoding="utf-8")
