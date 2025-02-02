import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

from anki.utils import checksum

from .anking_notetypes import anking_notetype_base_name
from .consts import USER_FILES_PATH
from .utils import read_text

def get_export_templates(notetype_name: str) -> List[Dict]:
    result = []
    for ord in existing_export_template_ords(notetype_name):
        result.append(
            {
                "name": "",
                "qfmt": read_text(get_export_template_paths(notetype_name, ord)[0]),
                "afmt": read_text(get_export_template_paths(notetype_name, ord)[1]),
                "ord": ord,
            }
        )
    return result


def get_export_styling(notetype_name: str) -> str:
    return read_text(create_styling_file_if_not_exists(notetype_name))


def get_export_styling_path(notetype_name: str) -> Path:
    templates_dir = create_templates_dir_if_not_exists(notetype_name)
    return templates_dir / "styling.css"


def get_export_template_paths(notetype_name: str, ord: int) -> Tuple[Path, Path]:
    templates_dir = create_templates_dir_if_not_exists(notetype_name)
    return (
        (templates_dir / f"card{ord}_front.html"),
        (templates_dir / f"card{ord}_back.html"),
    )


def existing_export_template_ords(notetype_name: str) -> List[int]:
    if not (templates_dir := (template_dir(notetype_name))).exists():
        return []
    result = []
    for front_path in templates_dir.glob("*_front.html"):
        m = re.match("card(\d+)_front.html", front_path.name)
        if not m:
            continue
        ord = int(m.group(1))
        if not (templates_dir / f"card{ord}_back.html").exists():
            continue
        result.append(ord)

    return sorted(result)


def create_templates_dir_if_not_exists(notetype_name: str):
    path = template_dir(notetype_name)
    if not path.exists():
        os.mkdir(path)
    return path


def template_dir(notetype_name: str) -> Path:
    if anking_notetype_base_name(notetype_name):
        return USER_FILES_PATH / anking_notetype_base_name(notetype_name)
    else:
        return USER_FILES_PATH / checksum(notetype_name)


def create_styling_file_if_not_exists(notetype_name: str) -> Path:
    result = get_export_styling_path(notetype_name)
    if not result.exists():
        result.touch()
    return result
