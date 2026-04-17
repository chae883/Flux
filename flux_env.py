import os
import nuke
import re
import config

# 環境変数のキー定義
ENV_KEY_ROOT = "FLUX_ROOT"
ENV_KEY_PROJECT = "FLUX_PROJECT"
ENV_KEY_SEQ = "FLUX_SEQ"
ENV_KEY_SHOT = "FLUX_SHOT"

def set_global_context(project=None, seq=None, shot=None):
    if project: os.environ[ENV_KEY_PROJECT] = project
    if seq:     os.environ[ENV_KEY_SEQ] = seq
    if shot:    os.environ[ENV_KEY_SHOT] = shot
    print(f"[Flux Env] Context Set: {project} / {seq} / {shot}")

def create_project_structure(project, shot):
    """
    Creates the directory structure for a new shot based on config.FOLDER_STRUCTURE.
    """
    base_root = os.environ.get(ENV_KEY_ROOT, config.BASE_ROOT)
    context = config.DEFAULT_CONTEXT
    
    # Construct shot root: e.g., D:/Studio/WIP/private/ProjectName/ShotName
    shot_path = config.normalize_path(os.path.join(base_root, context, project, shot))
    
    created_paths = []
    
    # Create main shot directory
    if not os.path.exists(shot_path):
        os.makedirs(shot_path)
        created_paths.append(shot_path)

    # Create sub-folders from config
    for folder in config.FOLDER_STRUCTURE:
        full_path = config.normalize_path(os.path.join(shot_path, folder))
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created_paths.append(full_path)
            
    # Always ensure _config exists
    config_dir = config.normalize_path(os.path.join(base_root, "_config"))
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    print(f"[Flux Env] Created {len(created_paths)} folders for {project}_{shot}")
    return shot_path

def update_env_from_script():
    """
    Context resolution logic.
    1. Trust existing env vars (if set by launcher).
    2. If not, try to resolve from script path.
    """
    # If already set, do nothing (Source of Truth)
    if os.environ.get(ENV_KEY_PROJECT) and os.environ.get(ENV_KEY_SHOT):
        return

    script_path = nuke.root().name()
    if script_path == 'Root':
        return

    path = config.normalize_path(script_path)
    
    # Determine Root
    # Try to see if path starts with known config.BASE_ROOT
    known_root = config.normalize_path(config.BASE_ROOT)
    
    if path.startswith(known_root):
        os.environ[ENV_KEY_ROOT] = known_root
    else:
        # Fallback: Assume standard structure and try to guess root?
        # For now, let's enforce BASE_ROOT if we can't guess, or rely on finding specific markers.
        pass

    # Regex Analysis: Look for private/Project/Shot/... or just Project/Shot/...
    # Assuming: .../[context]/[project]/[shot]/scripts/...
    # We look for the 'scripts' folder as an anchor.
    
    pattern = r"(?P<project>[^/]+)/(?P<shot>[^/]+)/scripts"
    match = re.search(pattern, path)
    
    if match:
        data = match.groupdict()
        project_name = data['project']
        shot_name = data['shot']
        
        parts = shot_name.split('_')
        seq_num = parts[1] if len(parts) >= 3 else ""

        # Set Env Vars
        os.environ[ENV_KEY_PROJECT] = project_name
        os.environ[ENV_KEY_SEQ] = seq_num
        os.environ[ENV_KEY_SHOT] = shot_name
        
        # If FLUX_ROOT was not set yet, try to derive it
        if not os.environ.get(ENV_KEY_ROOT):
            # Calculate root by stripping everything after project
            # path is .../Project/Shot/scripts/...
            # We want .../ (before project)
            # But wait, there is [context] usually.
            
            # Simple approach: config.BASE_ROOT is the intended root.
            os.environ[ENV_KEY_ROOT] = config.BASE_ROOT
        
        print(f"[Flux Env] Auto-detected Context from Path: {project_name} > {shot_name}")
    else:
        print(f"[Flux Env] Warning: Could not detect context from path. Env vars not set.")

def get_context():
    return {
        "root": os.environ.get(ENV_KEY_ROOT, config.BASE_ROOT),
        "project": os.environ.get(ENV_KEY_PROJECT, ""),
        "seq": os.environ.get(ENV_KEY_SEQ, ""),
        "shot": os.environ.get(ENV_KEY_SHOT, "")
    }