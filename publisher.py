import nuke
import os
import shutil
import datetime
import config
import flux_env

def publish_current_script():
    """
    Publishes the current script.
    1. Checks if the script is saved.
    2. Determines the 'published' directory based on the current context.
    3. Copies the current script to the 'published' directory.
    4. Optionally versions up the work file to prepare for the next task.
    """
    
    # 1. Validation
    if nuke.root().name() == 'Root':
        nuke.message("Please save your work file first.")
        return

    script_path = nuke.root().name()
    
    # Ensure we are in a valid Flux context
    if not flux_env.get_context()['project']:
        flux_env.update_env_from_script()
        if not flux_env.get_context()['project']:
             nuke.message("Could not determine Flux Context. Publish aborted.")
             return

    # 2. Path Construction
    # Assumes structure: .../shot/scripts/work/shot_v001.nk
    # Target: .../shot/scripts/published/shot_v001_published.nk
    
    current_dir = os.path.dirname(script_path)
    # Go up one level from 'work' to 'scripts', then down to 'published'
    # This logic assumes the folder structure defined in config.json
    
    # Check if we are in a 'work' folder
    if os.path.basename(current_dir) != 'work':
        # If not in 'work', assume we are in 'scripts' root or somewhere else.
        # Try to find a sibling 'published' folder.
        parent_dir = os.path.dirname(current_dir)
        publish_dir = os.path.join(parent_dir, 'published').replace('\\', '/')
    else:
        parent_dir = os.path.dirname(current_dir)
        publish_dir = os.path.join(parent_dir, 'published').replace('\\', '/')

    if not os.path.exists(publish_dir):
        try:
            os.makedirs(publish_dir)
        except OSError:
            nuke.message(f"Could not create publish directory:\n{publish_dir}")
            return

    filename = os.path.basename(script_path)
    name, ext = os.path.splitext(filename)
    
    # Add a timestamp or just keep the version?
    # Standard practice: Keep the version match. work v001 -> publish v001.
    # This creates a traceable link.
    
    publish_filename = f"{name}_published{ext}"
    publish_path = os.path.join(publish_dir, publish_filename).replace('\\', '/')

    # 3. Publish Action
    if os.path.exists(publish_path):
        if not nuke.ask(f"Publish file already exists:\n{publish_path}\n\nOverwrite?"):
            return

    try:
        # Save the current work file first to ensure latest changes are on disk
        nuke.scriptSave()
        
        # Copy to publish location
        shutil.copy2(script_path, publish_path)
        
        # Lock the file (Read-Only)
        try:
            # S_IREAD: Owner read, S_IRGRP: Group read, S_IROTH: Others read
            import stat
            os.chmod(publish_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
        except Exception as e:
            print(f"Warning: Could not set read-only permission: {e}")

        # 4. Success & Post-Publish Actions
        msg = f"Successfully Published:\n{publish_path}\n\nFile is now Locked (Read-Only)."
        
        # Optional: Version up the work file automatically
        if nuke.ask(msg + "\n\nDo you want to Version Up your work file now?"):
            import version_up
            version_up.run()
            
    except Exception as e:
        nuke.message(f"Publish failed:\n{e}")