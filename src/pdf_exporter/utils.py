import subprocess
from pathlib import Path
from .compat import add_compat_aliases

add_compat_aliases()

from anki.utils import is_mac, is_win
from aqt.qt import *


def open_link(path):
    if is_win or is_mac:
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
    else:
        subprocess.Popen(("xdg-open", Path(path).as_uri()))


def open_file(path):
    if is_win:
        try:
            os.startfile(path)
        except (OSError, UnicodeDecodeError):
            pass
    elif is_mac:
        subprocess.call(("open", path))
    else:
        subprocess.call(("xdg-open", path))
