import nuke
import os
import platform
import re
import datetime
import config
import validator
import flux_env
import traceback

# ------------------------------------------------------------------------------
# PATH CALCULATION
# ------------------------------------------------------------------------------

def get_script_version():
    script_name = nuke.root().name()
    if script_name == 'Root': return None
    match = re.search(r'[vV](\d+)', os.path.basename(script_name))
    if match:
        return f"v{int(match.group(1)):03d}"
    return None

def get_write_path(node=None):
    if node is None:
        try:
            node = nuke.thisNode()
            if node.name() == 'Write_Internal': node = node.parent()
        except: return ""

    # Ensure context is loaded
    if not os.environ.get('FLUX_PROJECT'):
        flux_env.update_env_from_script()

    # Get Context
    project = os.environ.get('FLUX_PROJECT', '')
    shot = os.environ.get('FLUX_SHOT', '')
    
    # Critical Check
    if not project or not shot:
        # Return a path that is obviously wrong to trigger Validator, but also safe from overwriting random files
        return f"[getenv FLUX_ROOT]/_ERROR_CONTEXT_NOT_SET_/renders/error.exr"

    root_path = "[getenv FLUX_ROOT]"

    try:
        mode = node['render_mode'].value()
        raw_cat = node['render_variant'].value()
        raw_lbl = node['render_label'].value()
        use_local_ver = node['use_local_version'].value()
        local_ver_int = int(node['local_version'].value())
    except: return ""

    cat_str = 'elm' if raw_cat == 'element' else ('' if raw_cat == '(Main)' else raw_cat)
    lbl_str = sanitize_text(raw_lbl)
    
    # --- Version Logic ---
    ver_str = ""
    is_main = (raw_cat == '(Main)')
    
    # Determine Enforcement
    # 1. Main Render + Strict Mode = Enforce
    # 2. All Render Strict Mode = Enforce
    should_enforce = (config.ENFORCE_VERSION_MATCH and is_main) or config.ENFORCE_ALL_VERSIONS
    
    if should_enforce:
        script_ver = get_script_version()
        if script_ver:
            ver_str = script_ver
        else:
            ver_str = f"v{local_ver_int:03d}"
    else:
        # Flexible Mode
        if use_local_ver:
            ver_str = f"v{local_ver_int:03d}"
    
    parts = [shot]
    if cat_str: parts.append(cat_str)
    if lbl_str: parts.append(lbl_str)
    if ver_str: parts.append(ver_str)
    
    filename_base = "_".join(parts)
    
    user_context = config.DEFAULT_CONTEXT 
    shot_dir = f"{root_path}/{user_context}/{project}/{shot}"

    path = ""
    if mode == 'Master (EXR)':
        ext = "exr"
        path = f"{shot_dir}/renders/{filename_base}/{filename_base}.%04d.{ext}"
    elif mode == 'Review (MOV)':
        ext = "mov"
        path = f"{shot_dir}/renders/dailies/{filename_base}.{ext}"
    elif mode == 'Temp (JPG)':
        ext = "jpg"
        # Resolve Temp Path in Python to ensure safety
        temp_root = config.TEMP_WINDOWS if platform.system() == 'Windows' else config.TEMP_LINUX
        # Use python-resolved path or env var if temp_root starts with C:/ etc
        # To match the style of [getenv], we can leave it hardcoded or use FLUX_TEMP if we trust it.
        # Let's trust FLUX_TEMP if set, otherwise fallback to config.
        # But for Nuke knob, we should try to use env var for portability if possible.
        # For now, let's use the resolved logic from config which handles FLUX_TEMP.
        
        path = f"{temp_root}/nuke_temp/{project}/{shot}/{filename_base}.%04d.{ext}"

    return path

def sanitize_text(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9_\-]', '', text)

# ------------------------------------------------------------------------------
# UI UPDATE
# ------------------------------------------------------------------------------

def update_flux_write(node=None):
    if node is None:
        try: node = nuke.thisNode()
        except: return

    with node:
        w = nuke.toNode('Write_Internal')
        if w:
            new_path_str = get_write_path(node)
            if w['file'].value() != new_path_str:
                w['file'].setValue(new_path_str)

    try:
        mode = node['render_mode'].value()
        raw_cat = node['render_variant'].value()
        is_main = (raw_cat == '(Main)')
        
        k_grp = [node.knob('use_local_version'), node.knob('ver_down'), node.knob('local_version'), node.knob('ver_up')]
        
        should_enforce = (config.ENFORCE_VERSION_MATCH and is_main) or config.ENFORCE_ALL_VERSIONS

        if should_enforce:
            # STRICT: Local controls hidden
            for k in k_grp: k.setVisible(False)
            node.knob('script_ver_up').setVisible(True)
            # ラベルで状態を明示 (Script Ver)
            node.knob('render_now').setLabel("Render (Script Ver)")
        else:
            # FLEXIBLE: Local controls shown
            if is_main:
                # Main but flexible (Rare config)
                for k in k_grp: k.setVisible(False) 
                node.knob('script_ver_up').setVisible(True)
                node.knob('render_now').setLabel("Render (Main)")
            else:
                # Precomps / Elements
                for k in k_grp: k.setVisible(True)
                node.knob('script_ver_up').setVisible(False)
                node.knob('render_now').setLabel("Render (Auto-Inc)" if node['use_local_version'].value() else "Render (Current)")

        is_mov = (mode == 'Review (MOV)')
        node.knob('use_burnin').setVisible(is_mov)
        
        with node:
            burn = nuke.toNode('BurnIn_Internal')
            if is_mov and node['use_burnin'].value():
                burn['disable'].setValue(False)
                
                # Get rich metadata
                ctx = flux_env.get_context()
                proj = ctx.get('project', 'UNK')
                shot = ctx.get('shot', 'UNK')
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                user = os.environ.get('USERNAME', 'user')
                
                burn_msg = f"{proj} | {shot} | {today}\nFrame: [frame]"
                # burn['message'].setValue(burn_msg)
                # Text2 needs proper formatting. 
                # Let's use simple top-left / top-right structure if possible, but Text2 is single block.
                # Just nice multi-line info.
                
                final_msg = f"PROJ: {proj}   SHOT: {shot}\nDATE: {today}   USER: {user}\nFRAME: [frame]"
                burn['message'].setValue(final_msg)
            else:
                burn['disable'].setValue(True)

        apply_format_settings(node, w, mode)
        
        if 'render_info' in node.knobs():
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
        
        # Enforce Logic Check
        should_enforce = (config.ENFORCE_VERSION_MATCH and is_main) or config.ENFORCE_ALL_VERSIONS

        if should_enforce:
            pass # Script version driven
        else:
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
        
        nuke.execute(node, start, end)
        
        try:
            with node: w_int = nuke.toNode('Write_Internal')
            import notification
            notification.show_notification(w_int, start_time, start, end)
        except: pass

    except RuntimeError as e:
        if "Cancelled" not in str(e):
            nuke.message(f"Render Error:\n{e}")

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