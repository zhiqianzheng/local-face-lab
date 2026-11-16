import os
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent

def data_dir():
    override = os.environ.get('FACE_LAB_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()
    if os.name == 'nt':
        root = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        root = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
    return root / 'local-face-lab'

def model_dir():
    override = os.environ.get('FACE_LAB_MODEL_DIR')
    if override:
        return Path(override).expanduser().resolve()
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'bundled_models'
    return data_dir() / 'models'
