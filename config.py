import json
import os
import nuke

# 設定ファイルのパス
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'flux_config.json')

_config_data = {}

def load_config():
    global _config_data
    if not os.path.exists(CONFIG_FILE):
        msg = f"[Flux Error] Config file not found at: {CONFIG_FILE}"
        if nuke.GUI:
            print(msg) 
        else:
            print(msg)
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            _config_data = json.load(f)
    except Exception as e:
        print(f"[Flux Error] Failed to parse config JSON: {e}")

load_config()

def get(section, key, default=None):
    return _config_data.get(section, {}).get(key, default)

def get_path(key, default=None):
    """
    パス取得。環境変数を優先的に使用する。
    例: FLUX_BASE_ROOT があれば JSON の base_root より優先される。
    """
    # 1. 環境変数によるオーバーライドを確認
    env_key = f"FLUX_{key.upper()}"
    if env_key in os.environ:
        return os.environ[env_key].replace('\\', '/')

    # 2. JSON設定からの取得
    raw_path = _config_data.get('paths', {}).get(key, default)
    if raw_path:
        raw_path = raw_path.replace('\\', '/')
        return os.path.expandvars(raw_path)
    
    return default

# --- Global Config Variables ---

WEBHOOK_URL = get('general', 'webhook_url', '')
PLAYER_PATH = get_path('player_executable', '')
FILE_EXPLORER_PATH = get_path('file_explorer_executable', '')

# --- Project Defaults ---
# 環境変数 FLUX_ROOT があればそれを最優先
BASE_ROOT = os.environ.get('FLUX_ROOT', get_path('base_root', "D:/Studio/WIP"))

ANCHORPOINT_PATH = get_path('anchorpoint_executable', "")
FOLDER_STRUCTURE = get('project_defaults', 'folder_structure', ['scripts', 'renders', 'plates', 'ref'])

DEFAULT_CONTEXT = get('project_defaults', 'context', 'private')
DEFAULT_PROJECT = get('project_defaults', 'project_code', 'TMP')

# --- Render Settings ---
RENDER_EXR = get('render_settings', 'exr', {})
RENDER_MOV = get('render_settings', 'mov', {})
RENDER_JPG = get('render_settings', 'jpg', {})

# Temp Paths - 環境変数を優先
TEMP_WINDOWS = os.environ.get('FLUX_TEMP', get_path('temp_windows', "C:/Temp"))
TEMP_LINUX = os.environ.get('FLUX_TEMP', get_path('temp_linux', "/tmp"))

# --- Loader Settings ---
_default_cs_map = {".exr": "ACES - ACEScg", ".jpg": "sRGB", ".png": "sRGB", ".mov": "sRGB"}
LOADER_COLORSPACE_MAP = get('loader_rules', 'colorspace_overrides', _default_cs_map)
LOADER_DISABLE_POSTAGE_STAMP = get('loader_rules', 'disable_postage_stamp', True)