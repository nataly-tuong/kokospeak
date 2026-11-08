"""Writable paths and bundled-tool discovery for source and frozen launches."""
from functools import lru_cache
from pathlib import Path
import os
import shutil
import sys


def user_data_dir():
    if sys.platform == 'darwin':
        return Path.home()/'Library'/'Application Support'/'KokoSpeak'
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData'/'Local')))/'KokoSpeak'
    return Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local'/'share')))/'kokospeak'


def generated_dir():
    override = os.environ.get('KOKOSPEAK_DATA_DIR')
    if override:
        return Path(override).expanduser().resolve()/'generated'
    if getattr(sys,'frozen',False):
        return user_data_dir()/'generated'
    return Path(__file__).resolve().parents[1]/'generated'


def client_dist():
    if getattr(sys,'frozen',False):
        return Path(sys._MEIPASS)/'client'/'dist'
    return Path(__file__).resolve().parents[2]/'client'/'dist'


@lru_cache(maxsize=1)
def ffmpeg_executable():
    configured = os.environ.get('KOKOSPEAK_FFMPEG_PATH')
    if configured:
        path = Path(configured).expanduser()
        return str(path) if path.is_file() and os.access(path,os.X_OK) else None
    installed = shutil.which('ffmpeg')
    if installed:
        return installed
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError,RuntimeError,OSError):
        return None
