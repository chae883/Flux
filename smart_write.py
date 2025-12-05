import nuke
import os
import platform
import re
import datetime
import config
import validator
import flux_env

# ------------------------------------------------------------------------------
# PATH CALCULATION (Edit-Time Baking)
# ------------------------------------------------------------------------------

def get_write_path(node=None):
    """
    Calculates the file path for the Write node.
    Returns a string containing TCL variables (e.g., [getenv FLUX_ROOT])
    to ensure portability across render farms and OS.
    """
    if node is None:
        try:
            node = nuke.thisNode()
            if node.name() == 'Write_Internal':
                node = node.parent()
        except:
            return ""

    # Ensure context is available for calculation
    if not os.environ.get('FLUX_PROJECT'):
        flux_env.update_env_from_script()

    # --- 1. Root Abstraction (The most critical part for Farms) ---
    # We use the TCL syntax for the root to allow OS-switching on render nodes.
    # Note: We do NOT resolve this to D:/ or /mnt/ here. We keep it abstract.
    root_path = "[getenv FLUX_ROOT]"
    
    # --- 2. Context Retrieval ---
    # We get the current values to build the filename, but we can also
    # use TCL for folder structure if we want to be very robust.
    # For this implementation, we will bake the current Project/Shot context
    # into the path, but keep the Root abstract.
    
    project = os.environ.get('FLUX_PROJECT', 'Unknown')
    shot = os.environ.get('FLUX_SHOT', 'Unknown')
    
    # Fallback for unsaved scripts
    if project == 'Unknown' or shot == 'Unknown':
        return f"{root_path}/_UNSAVED_/{shot}/renders/unknown.exr"

    try:
        mode = node['render_mode'].value()
        raw_cat = node['render_variant'].value()
        raw_lbl = node['render_label'].value()
        use_local_ver = node['use_local_version'].value()
        local_ver_int = int(node['local_version'].value())
    except:
        return ""

    # --- 3. Filename Logic ---
    cat_str = 'elm' if raw_cat == 'element' else ('' if raw_cat == '(Main)' else raw_cat)
    lbl_str = sanitize_text(raw_lbl)
    
    # Version padding v001
    ver_str = f"v{local_ver_int:03d}" if use_local_ver else ""
    
    # Construct Filename Base: shot_variant_label_version
    parts = [shot]
    if cat_str: parts.append(cat_str)
    if lbl_str: parts.append(lbl_str)
    if ver_str: parts.append(ver_str)
    
    filename_base = "_".join(parts)
    
    # --- 4. Directory Structure Construction ---
    # Structure: ROOT / Context / Project / Shot / ...
    user_context = config.DEFAULT_CONTEXT 
    
    # We construct the base directory using the Abstract Root
    shot_dir = f"{root_path}/{user_context}/{project}/{shot}"

    path = ""
    if mode == 'Master (EXR)':
        ext = "exr"
        # Path: .../shot/renders/filename/filename.####.exr
        path = f"{shot_dir}/renders/{filename_base}/{filename_base}.%04d.{ext}"
        
    elif mode == 'Review (MOV)':
        ext = "mov"
        # Path: .../shot/renders/dailies/filename.mov
        path = f"{shot_dir}/renders/dailies/{filename_base}.{ext}"
        
    elif mode == 'Temp (JPG)':
        ext = "jpg"
        # For Temp, we might want local paths, but for safety we can use the FLUX_TEMP env var if it exists,
        # otherwise fall back to a hardcoded logic or a separate env var.
        # To be farm-safe, let's use a TCL var for temp as well if possible, 
        # or just assume the farm handles standard temp paths.
        
        # NOTE: If FLUX_TEMP is not set on the farm, this might fail. 
        # Ideally, we define FLUX_TEMP in the farm submission environment too.
        temp_root = "[getenv FLUX_TEMP]" 
        path = f"{temp_root}/nuke_temp/{project}/{shot}/{filename_base}.%04d.{ext}"

    return path

def sanitize_text(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9_\-]', '', text)

# ------------------------------------------------------------------------------
# UI UPDATE & SETUP
# ------------------------------------------------------------------------------

def update_flux_write(node=None):
    """
    Triggered on KnobChanged.
    Calculates the path string (Edit-Time Baking) and sets it to the File knob.
    """
    if node is None:
        try: node = nuke.thisNode()
        except: return

    # 1. Update the File Path (The Core Logic Change)
    with node:
        w = nuke.toNode('Write_Internal')
        if w:
            # Calculate the safe path string (containing [getenv ...])
            # This runs Python NOW, not at render time.
            new_path_str = get_write_path(node)
            
            # Update the knob only if it changed to prevent recursive loops/performance hits
            if w['file'].value() != new_path_str:
                w['file'].setValue(new_path_str)

    # 2. UI Visibility & Format Logic (Same as before)
    try:
        mode = node['render_mode'].value()
        raw_cat = node['render_variant'].value()
        is_main = (raw_cat == '(Main)')
        
        k_grp = [node.knob('use_local_version'), node.knob('ver_down'), node.knob('local_version'), node.knob('ver_up')]
        if is_main:
            for k in k_grp: k.setVisible(False)
            node.knob('script_ver_up').setVisible(True)
            node.knob('render_now').setLabel("Render (Main)")
        else:
            for k in k_grp: k.setVisible(True)
            node.knob('script_ver_up').setVisible(False)
            node.knob('render_now').setLabel("Render (Auto-Inc)" if node['use_local_version'].value() else "Render (Current)")

        is_mov = (mode == 'Review (MOV)')
        node.knob('use_burnin').setVisible(is_mov)
        
        with node:
            burn = nuke.toNode('BurnIn_Internal')
            if is_mov and node['use_burnin'].value():
                burn['disable'].setValue(False)
                # For visual feedback in Nuke GUI, we evaluate the abstract path to a real path
                # so the BurnIn node shows something useful, not "[getenv FLUX_ROOT]..."
                # However, BurnIn needs to render on the farm too. 
                # Ideally, BurnIn accepts TCL. Let's check.
                # Yes, BurnIn handles TCL. We can just pass the filename base.
                
                # Extract filename for display
                full_path = w['file'].value()
                filename = os.path.basename(full_path).split('.')[0] # Rough parsing
                
                # We can use TCL in the message to be safe
                # "[file tail [value parent.Write_Internal.file]]" is the robust Nuke way
                burn['message'].setValue(f"{filename} | Frame: [frame]")
            else:
                burn['disable'].setValue(True)

        apply_format_settings(node, w, mode)
        
        # Update Info Knob (Resolved path for user verification)
        if 'render_info' in node.knobs():
            # We evaluate the TCL to show the user the *Real* path on their current machine
            resolved_path = nuke.tcl('subst', w['file'].value())
            node['render_info'].setValue(f"Target: {os.path.basename(resolved_path)}")

    except Exception:
        pass

def apply_format_settings(node, w, mode):
    root_working = nuke.root()['workingSpaceLUT'].value() 
    def set_cs(target, keywords=[]):
        try:
            if target and "color_picking" not in target:
                w['colorspace'].setValue(target)
                return
        except: pass
        for kw in keywords:
            for cs in w['colorspace'].values():
                if "color_picking" in cs.lower(): continue
                if kw.lower() in cs.lower():
                    try: w['colorspace'].setValue(cs); return
                    except: pass

    if mode == 'Master (EXR)':
        w['transformType'].setValue('colorspace')
        st = config.RENDER_EXR
        w['file_type'].setValue('exr')
        w['datatype'].setValue(st.get('datatype', '32 bit float'))
        w['compression'].setValue(st.get('compression', 'Zip (1 scanline)'))
        w['views'].setValue('main'); w['channels'].setValue('rgb')
        set_cs(root_working, ['default', 'scene_linear', 'ACES - ACEScg', 'ACEScg'])
        node['tile_color'].setValue(0x44aa44ff)

    elif mode == 'Review (MOV)':
        w['transformType'].setValue('display')
        w['file_type'].setValue('mov')
        st = config.RENDER_MOV
        try:
            w['mov64_codec'].setValue(st.get('codec', 'appr'))
            w['mov_prores_codec_profile'].setValue(st.get('prores_profile', 'ProRes 4:4:4:4 XQ 12-bit'))
            w['mov64_quality'].setValue(st.get('quality', 'High'))
        except: pass
        w['views'].setValue('main'); w['channels'].setValue('rgb')
        try: w['ocioDisplay'].setValue('sRGB - Display'); w['ocioView'].setValue('ACES 1.0 - SDR Video')
        except: pass
        node['tile_color'].setValue(0x4488aaff)

    elif mode == 'Temp (JPG)':
        w['transformType'].setValue('display')
        w['file_type'].setValue('jpeg')
        try: w['_jpeg_quality'].setValue(config.RENDER_JPG.get('quality', 1.0))
        except: pass
        w['views'].setValue('main'); w['channels'].setValue('rgb')
        node['tile_color'].setValue(0xaa4444ff)

# ------------------------------------------------------------------------------
# ACTIONS
# ------------------------------------------------------------------------------

def render_with_auto_increment():
    node = nuke.thisNode()
    
    try:
        raw_cat = node['render_variant'].value()
        is_main = (raw_cat == '(Main)')
        if not is_main and node['use_local_version'].value():
            ver_k = node['local_version']
            ver_k.setValue(int(ver_k.value()) + 1)
    except: pass

    # Validator
    start = int(nuke.root().firstFrame())
    end = int(nuke.root().lastFrame())
    if node.input(0):
        start = int(node.input(0).firstFrame())
        end = int(node.input(0).lastFrame())

    if not validator.validate_render(node, start, end): return
        
    try:
        print(f"Flux Render: Frames {start}-{end}")
        start_time = datetime.datetime.now()
        
        # Execute Render
        # Because the path is now baked string with TCL vars, nuke.execute works perfectly locally
        # and on the farm.
        nuke.execute(node, start, end)
        
        try:
            with node: w_int = nuke.toNode('Write_Internal')
            import notification
            notification.show_notification(w_int, start_time, start, end)
        except: pass

    except RuntimeError as e:
        if "Cancelled" not in str(e):
            nuke.message(f"Render Error:\n{e}")

# Helper wrappers
def local_version_up(node):
    k = node['local_version']
    k.setValue(int(k.value()) + 1)
def local_version_down(node):
    k = node['local_version']
    val = int(k.value())
    if val > 1: k.setValue(val - 1)
def script_version_up_wrapper():
    try: import version_up; version_up.run()
    except: nuke.message("Version up script error")

def create_flux_write():
    if not flux_env.get_context()['project']:
        flux_env.update_env_from_script()
        
    group = nuke.createNode('Group')
    group.setName('FluxWrite')
    group['tile_color'].setValue(0x44aa44ff)
    
    k_tab = nuke.Tab_Knob('Flux_Tab', 'Flux Settings')
    group.addKnob(k_tab)
    
    modes = ['Master (EXR)', 'Review (MOV)', 'Temp (JPG)']
    k_mode = nuke.Enumeration_Knob('render_mode', 'Render Mode', modes)
    group.addKnob(k_mode)
    
    variants = ['(Main)', 'precomp', 'matte', 'bg', 'fg', 'element', 'denoise', 'tech']
    k_tag = nuke.Enumeration_Knob('render_variant', 'Content Type', variants)
    k_tag.setFlag(nuke.STARTLINE)
    group.addKnob(k_tag)

    k_lbl = nuke.String_Knob('render_label', '')
    k_lbl.clearFlag(nuke.STARTLINE)
    group.addKnob(k_lbl)
    
    group.addKnob(nuke.Text_Knob('div1', ''))

    k_burn = nuke.Boolean_Knob('use_burnin', 'Burn-in Info')
    k_burn.setValue(True); k_burn.setFlag(nuke.STARTLINE)
    group.addKnob(k_burn)

    k_scr = nuke.PyScript_Knob('script_ver_up', 'Script Version Up (Save As...)', "import smart_write\nsmart_write.script_version_up_wrapper()")
    k_scr.setFlag(nuke.STARTLINE); k_scr.setVisible(False)
    group.addKnob(k_scr)

    k_use = nuke.Boolean_Knob('use_local_version', 'Use Local Version')
    k_use.setFlag(nuke.STARTLINE); k_use.setVisible(False)
    group.addKnob(k_use)

    k_down = nuke.PyScript_Knob('ver_down', ' - ', "import smart_write\nsmart_write.local_version_down(nuke.thisNode())")
    k_down.clearFlag(nuke.STARTLINE); k_down.setVisible(False)
    group.addKnob(k_down)

    k_ver = nuke.Int_Knob('local_version', '')
    k_ver.setValue(1); k_ver.clearFlag(nuke.STARTLINE); k_ver.setVisible(False)
    group.addKnob(k_ver)

    k_up = nuke.PyScript_Knob('ver_up', ' + ', "import smart_write\nsmart_write.local_version_up(nuke.thisNode())")
    k_up.clearFlag(nuke.STARTLINE); k_up.setVisible(False)
    group.addKnob(k_up)

    group.addKnob(nuke.Text_Knob('div2', ''))

    k_ren = nuke.PyScript_Knob('render_now', 'Render', "import smart_write\nsmart_write.render_with_auto_increment()")
    k_ren.setFlag(nuke.STARTLINE)
    group.addKnob(k_ren)
    
    # Path Revealer
    # Note: We use nuke.tcl('subst', ...) to resolve the path before opening the folder
    open_code = "import os, sys, subprocess; n=nuke.thisNode(); w=nuke.toNode('Write_Internal'); p=nuke.tcl('subst', w['file'].value()); f=os.path.dirname(p); os.startfile(f) if sys.platform=='win32' else subprocess.Popen(['open', f]) if sys.platform=='darwin' else subprocess.Popen(['xdg-open', f])"
    group.addKnob(nuke.PyScript_Knob('reveal', 'Open Folder', open_code))

    group.addKnob(nuke.Text_Knob('div3', '')) 
    k_info = nuke.Text_Knob('render_info', 'Current Settings:')
    k_info.setValue('Initializing...')
    group.addKnob(k_info)

    with group:
        inp = nuke.createNode('Input')
        burn = nuke.createNode('Text2', 'name BurnIn_Internal box {0 0 1920 80} xjustify center yjustify bottom global_font_scale 0.4 enable_background true background_opacity 0.6', False)
        w = nuke.createNode('Write', 'name Write_Internal create_directories true', False)
        out = nuke.createNode('Output')
        burn.setInput(0, inp); w.setInput(0, burn); out.setInput(0, w)

    group['knobChanged'].setValue("try:\n import smart_write\n smart_write.update_flux_write()\nexcept: pass")
    update_flux_write(group)