import json
import os
import nuke

# 設定ファイルのパス
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'flux_config.json')

_config_data = {}

def load_config():
    global _config_data
    if not os.path.exists(CONFIG_FILE):
        # 致命的なエラーなのでポップアップを出す推奨
        msg = f"[Flux Error] Config file not found at:\n{CONFIG_FILE}\nPlease check installation."
        if nuke.GUI:
            nuke.message(msg)
        else:
            print(msg)
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            _config_data = json.load(f)
    except Exception as e:
        msg = f"[Flux Error] Failed to parse config JSON:\n{e}"
        if nuke.GUI:
            nuke.message(msg)
        print(msg)

load_config()

def get(section, key, default=None):
    return _config_data.get(section, {}).get(key, default)

def get_path(key, default=None):
    """
    パス取得時に環境変数を展開する。
    FLUX_ROOTなどの独自変数もここで解決可能。
    """
    raw_path = _config_data.get('paths', {}).get(key, default)
    if raw_path:
        # Windowsパスのバックスラッシュ対策
        raw_path = raw_path.replace('\\', '/')
        return os.path.expandvars(raw_path)
    return default

# --- Global Config Variables ---

WEBHOOK_URL = get('general', 'webhook_url', '')
PLAYER_PATH = get_path('player_executable', '')
FILE_EXPLORER_PATH = get_path('file_explorer_executable', '')

# --- Project Defaults ---
# 環境変数 FLUX_ROOT があればそれを優先、なければJSONの値を使う
BASE_ROOT = os.environ.get('FLUX_ROOT', get_path('base_root', "D:/Studio/WIP"))

ANCHORPOINT_PATH = get_path('anchorpoint_executable', "")
FOLDER_STRUCTURE = get('project_defaults', 'folder_structure', ['scripts', 'renders', 'plates', 'ref'])

DEFAULT_FORMAT = get('project_defaults', 'format', '4K_DCP')
DEFAULT_WIDTH = get('project_defaults', 'width', 4096)
DEFAULT_HEIGHT = get('project_defaults', 'height', 2160)
DEFAULT_FPS = get('project_defaults', 'fps', 24.0)
DEFAULT_START = get('project_defaults', 'frame_start', 1001)
DEFAULT_END = get('project_defaults', 'frame_end', 1100)
DEFAULT_CONTEXT = get('project_defaults', 'context', 'private')
DEFAULT_PROJECT = get('project_defaults', 'project_code', 'TMP')

# --- Render Settings ---
RENDER_EXR = get('render_settings', 'exr', {})
RENDER_MOV = get('render_settings', 'mov', {})
RENDER_JPG = get('render_settings', 'jpg', {})
TEMP_WINDOWS = get_path('temp_windows', "C:/Temp")
TEMP_LINUX = get_path('temp_linux', "/tmp")

# --- Loader Settings ---
_default_cs_map = {".exr": "ACES - ACEScg", ".jpg": "sRGB", ".png": "sRGB", ".mov": "sRGB"}
LOADER_COLORSPACE_MAP = get('loader_rules', 'colorspace_overrides', _default_cs_map)
LOADER_DISABLE_POSTAGE_STAMP = get('loader_rules', 'disable_postage_stamp', True)