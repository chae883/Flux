import json
import os
import nuke

def normalize_path(path):
    """Normalize file paths to use forward slashes for cross-platform compatibility."""
    if not path:
        return path
    return path.replace('\\', '/')
    

class FluxConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FluxConfig, cls).__new__(cls)
            cls._instance.load()
        return cls._instance

    def __init__(self):
        pass

    def load(self):
        self.config_path = os.path.join(os.path.dirname(__file__), 'flux_config.json')
        self.data = {}
        
        if not os.path.exists(self.config_path):
            self.log_error(f"Config file not found at: {self.config_path}")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            self.log_error(f"Failed to parse config JSON: {e}")

    def get(self, section, key, default=None):
        return self.data.get(section, {}).get(key, default)

    def get_path(self, key, default=None):
        env_key = f"FLUX_{key.upper()}"
        if env_key in os.environ:
            return normalize_path(os.environ[env_key])
        
        raw_path = self.data.get('paths', {}).get(key, default)
        if raw_path:
            raw_path = normalize_path(raw_path)
            return os.path.expandvars(raw_path)
        return default

    def get_webhook_url(self):
        env_url = os.environ.get("FLUX_DISCORD_WEBHOOK")
        if env_url: return env_url
        return self.get('general', 'webhook_url', '')

    def log_error(self, message):
        formatted_msg = f"[Flux Config Error] {message}"
        if nuke.GUI: print(formatted_msg)
        else: print(formatted_msg)

conf = FluxConfig()

# --- Public API ---
WEBHOOK_URL = conf.get_webhook_url()
PLAYER_PATH = conf.get_path('player_executable', '')
FILE_EXPLORER_PATH = conf.get_path('file_explorer_executable', '')

BASE_ROOT = os.environ.get('FLUX_ROOT', conf.get_path('base_root', "D:/Studio/WIP"))
ANCHORPOINT_PATH = conf.get_path('anchorpoint_executable', "")
FOLDER_STRUCTURE = conf.get('project_defaults', 'folder_structure', ['scripts', 'renders', 'plates', 'ref'])

DEFAULT_FORMAT = conf.get('project_defaults', 'format', '4K_DCP')
DEFAULT_WIDTH = conf.get('project_defaults', 'width', 4096)
DEFAULT_HEIGHT = conf.get('project_defaults', 'height', 2160)
DEFAULT_FPS = conf.get('project_defaults', 'fps', 24.0)
DEFAULT_START = conf.get('project_defaults', 'frame_start', 1001)
DEFAULT_END = conf.get('project_defaults', 'frame_end', 1100)
DEFAULT_CONTEXT = conf.get('project_defaults', 'context', 'private')
DEFAULT_PROJECT = conf.get('project_defaults', 'project_code', 'TMP')
DEFAULT_OCIO_CONFIG = conf.get('project_defaults', 'ocio_config_path', 'nuke-default')

# Strict Versioning Rules (TD Feedback: Default to True for safety)
ENFORCE_VERSION_MATCH = conf.get('project_defaults', 'enforce_script_version_match', True)
ENFORCE_ALL_VERSIONS = conf.get('project_defaults', 'enforce_all_render_versions', True)

RENDER_EXR = conf.get('render_settings', 'exr', {})
RENDER_MOV = conf.get('render_settings', 'mov', {})
RENDER_JPG = conf.get('render_settings', 'jpg', {})

TEMP_WINDOWS = os.environ.get('FLUX_TEMP', conf.get_path('temp_windows', "C:/Temp"))
TEMP_LINUX = os.environ.get('FLUX_TEMP', conf.get_path('temp_linux', "/tmp"))

_default_cs_map = {".exr": "ACES - ACEScg", ".jpg": "Output - sRGB", ".mov": "Output - Rec.709"}
LOADER_COLORSPACE_MAP = conf.get('loader_rules', 'colorspace_overrides', _default_cs_map)
LOADER_DISABLE_POSTAGE_STAMP = conf.get('loader_rules', 'disable_postage_stamp', True)