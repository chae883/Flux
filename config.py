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
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            _config_data = json.load(f)
    except Exception as e:
        print(f"[Flux Error] Failed to parse config JSON: {e}")

# 初回ロード
load_config()

# ヘルパー関数
def get(section, key, default=None):
    return _config_data.get(section, {}).get(key, default)

def get_path(key, default=None):
    # 環境変数を優先 (FLUX_KEY)
    env_key = f"FLUX_{key.upper()}"
    if env_key in os.environ:
        return os.environ[env_key].replace('\\', '/')
    
    # JSONから取得して展開
    raw_path = _config_data.get('paths', {}).get(key, default)
    if raw_path:
        raw_path = raw_path.replace('\\', '/')
        return os.path.expandvars(raw_path)
    return default

# --- Global Config Variables (安全に定義) ---

WEBHOOK_URL = get('general', 'webhook_url', '')
PLAYER_PATH = get_path('player_executable', '')
FILE_EXPLORER_PATH = get_path('file_explorer_executable', '')

# Project Defaults
# 環境変数を最優先、次にJSON、最後にハードコードされたデフォルト
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
DEFAULT_OCIO_CONFIG = get('project_defaults', 'ocio_config_path', 'nuke-default')

# Strict Versioning Rule
ENFORCE_VERSION_MATCH = get('project_defaults', 'enforce_script_version_match', True)

# Render Settings
RENDER_EXR = get('render_settings', 'exr', {})
RENDER_MOV = get('render_settings', 'mov', {})
RENDER_JPG = get('render_settings', 'jpg', {})

# Temp Paths
TEMP_WINDOWS = os.environ.get('FLUX_TEMP', get_path('temp_windows', "C:/Temp"))
TEMP_LINUX = os.environ.get('FLUX_TEMP', get_path('temp_linux', "/tmp"))

# Loader Settings
_default_cs_map = {".exr": "ACES - ACEScg", ".jpg": "Output - sRGB", ".mov": "Output - Rec.709"}
LOADER_COLORSPACE_MAP = get('loader_rules', 'colorspace_overrides', _default_cs_map)
LOADER_DISABLE_POSTAGE_STAMP = get('loader_rules', 'disable_postage_stamp', True)