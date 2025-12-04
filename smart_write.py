import nuke
import os
import platform
import re
import datetime
import config
import validator

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------

def get_script_root_name():
    root_name = nuke.root().name()
    if root_name == 'Root': return None
    return os.path.splitext(os.path.basename(root_name))[0]

def sanitize_text(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9_\-]', '', text)

def local_version_up(node):
    k = node['local_version']
    k.setValue(int(k.value()) + 1)
    update_flux_write(node)

def local_version_down(node):
    k = node['local_version']
    val = int(k.value())
    if val > 1:
        k.setValue(val - 1)
        update_flux_write(node)

def bake_path(node):
    """手動Bake用"""
    with node:
        w_internal = nuke.toNode('Write_Internal')
        current_path = w_internal['file'].evaluate()
    
    if not current_path: return

    if not nuke.ask(f"Bake Path to Static?\n\n{current_path}"): return

    w_internal['file'].setValue(current_path)
    node['render_mode'].setEnabled(False)
    node['render_variant'].setEnabled(False)
    node['render_label'].setEnabled(False)
    node['label'].setValue(f"LOCKED (Static Path)\n{os.path.basename(current_path)}")
    node['tile_color'].setValue(0x555555ff)

# ------------------------------------------------------------------------------
# CORE LOGIC
# ------------------------------------------------------------------------------

def update_flux_write(node=None):
    if node is None:
        try: node = nuke.thisNode()
        except: return

    if not node['render_mode'].enabled(): return # Baked

    # Trigger Guard
    trigger_knobs = ['render_mode', 'render_variant', 'render_label', 'use_local_version', 'local_version', 'showPanel', 'use_burnin']
    try:
        k = nuke.thisKnob()
        if k and k.name() not in trigger_knobs: return
    except: pass

    script_name = get_script_root_name()
    if not script_name:
        node['label'].setValue("⚠️ SCRIPT NOT SAVED ⚠️")
        return

    try:
        mode = node['render_mode'].value()      
        raw_cat = node['render_variant'].value()
        raw_lbl = node['render_label'].value()
        use_local_ver = node['use_local_version'].value()
        local_ver_int = int(node['local_version'].value())
        use_burnin = node['use_burnin'].value()
    except ValueError: return 

    # UI Control
    is_main = (raw_cat == '(Main)')
    k_grp = [node.knob('use_local_version'), node.knob('ver_down'), node.knob('local_version'), node.knob('ver_up')]
    
    if is_main:
        for k in k_grp: k.setVisible(False)
        node.knob('script_ver_up').setVisible(True)
        node.knob('render_now').setLabel("Render (Main)")
        use_local_ver = False 
    else:
        for k in k_grp: k.setVisible(True)
        node.knob('script_ver_up').setVisible(False)
        node.knob('render_now').setLabel("Render (Auto-Inc)" if use_local_ver else "Render (Current)")

    is_mov = (mode == 'Review (MOV)')
    node.knob('use_burnin').setVisible(is_mov)

    with node:
        w = nuke.toNode('Write_Internal')
        burn = nuke.toNode('BurnIn_Internal')
    if not w or not burn: return 

    # Path Generation
    cat_str = 'elm' if raw_cat == 'element' else ('' if raw_cat == '(Main)' else raw_cat)
    lbl_str = sanitize_text(raw_lbl)
    parts = [p for p in [cat_str, lbl_str] if p]
    ver_suffix = f"_v{local_ver_int:03d}" if use_local_ver else ""
    
    mid = "_".join(parts)
    suffix = (f"_{mid}" if mid else "") + ver_suffix
    
    base_tcl = "[file rootname [file tail [value root.name]]]"
    final_name = f"{base_tcl}{suffix}"

    render_dir = "[file dirname [value root.name]]/../renders"
    temp_root = config.TEMP_WINDOWS if platform.system() == 'Windows' else config.TEMP_LINUX

    # Burn-in
    if is_mov and use_burnin:
        burn['disable'].setValue(False)
        burn['message'].setValue(f"{final_name}  |  Frame: [frame]")
    else:
        burn['disable'].setValue(True)

    # Colorspace Helper
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

    # Apply Settings
    if mode == 'Master (EXR)':
        w['transformType'].setValue('colorspace')
        w['file'].setValue(f"{render_dir}/{final_name}/{final_name}.%04d.exr")
        
        st = config.RENDER_EXR
        w['file_type'].setValue('exr')
        w['datatype'].setValue(st.get('datatype', '32 bit float'))
        w['compression'].setValue(st.get('compression', 'Zip (1 scanline)'))
        w['views'].setValue('main'); w['channels'].setValue('rgb')
        set_cs(root_working, ['default', 'scene_linear', 'ACES - ACEScg', 'ACEScg'])
        node['tile_color'].setValue(0x44aa44ff)
        node['label'].setValue(f"EXR (32f)\n{script_name}\n[{suffix.lstrip('_')}]")

    elif mode == 'Review (MOV)':
        w['transformType'].setValue('display')
        w['file'].setValue(f"{render_dir}/dailies/{final_name}.mov")
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
        node['label'].setValue(f"MOV (Review)\n{script_name}\n[{suffix.lstrip('_')}]")

    elif mode == 'Temp (JPG)':
        w['transformType'].setValue('display')
        w['file'].setValue(f"{temp_root}/nuke_temp/{script_name}/{script_name}{suffix}.%04d.jpg")
        w['file_type'].setValue('jpeg')
        try: w['_jpeg_quality'].setValue(config.RENDER_JPG.get('quality', 1.0))
        except: pass
        w['views'].setValue('main'); w['channels'].setValue('rgb')
        node['tile_color'].setValue(0xaa4444ff)
        node['label'].setValue(f"TEMP (JPG)\n{script_name}\n[{suffix.lstrip('_')}]")

    if 'render_info' in node.knobs():
        node['render_info'].setValue(f"File: {os.path.basename(w['file'].value())}")

# ------------------------------------------------------------------------------
# RENDER ACTION
# ------------------------------------------------------------------------------

def render_with_auto_increment():
    node = nuke.thisNode()
    
    # Auto-Increment Logic (Only if dynamic)
    if node['render_mode'].enabled():
        try:
            raw_cat = node['render_variant'].value()
            is_main = (raw_cat == '(Main)')
            if not is_main and node['use_local_version'].value():
                ver_k = node['local_version']
                ver_k.setValue(int(ver_k.value()) + 1)
                update_flux_write(node)
        except: pass

    # Validator Check
    start = int(nuke.root().firstFrame())
    end = int(nuke.root().lastFrame())
    if node.input(0):
        start = int(node.input(0).firstFrame())
        end = int(node.input(0).lastFrame())

    if not validator.validate_render(node, start, end): return
        
    # --- AUTO-BAKE (Pre-Render) ---
    # レンダリング直前にパスを確定(Bake)させ、終了後に戻す
    # これによりファームやバックグラウンド処理でのパス解決エラーを防ぐ
    
    with node:
        w_internal = nuke.toNode('Write_Internal')
        # 現在のTCL式を含んだパスを保持
        original_file_str = w_internal['file'].value()
        
        # 評価済みの静的パスを取得
        baked_path = w_internal['file'].evaluate()
        
        # 静的パスをセット (一時的)
        w_internal['file'].setValue(baked_path)
        print(f"[Flux] Auto-Baked path for render: {baked_path}")

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
            
    finally:
        # --- RESTORE (Post-Render) ---
        # レンダリング終了後（成功・失敗問わず）に元のTCL式に戻す
        with node:
            w_internal = nuke.toNode('Write_Internal')
            # 念のため、現在がBake状態か確認してから戻す
            if w_internal['file'].value() == baked_path:
                w_internal['file'].setValue(original_file_str)
                print("[Flux] Restored dynamic path expression.")
            
            # Groupノードの表示更新（念のため）
            update_flux_write(node)

# ------------------------------------------------------------------------------
# NODE CREATION
# ------------------------------------------------------------------------------

def create_flux_write():
    if not get_script_root_name():
        nuke.message("⚠️ Please Save Script First!")
        return

    group = nuke.createNode('Group')
    group.setName('FluxWrite')
    group['tile_color'].setValue(0x44aa44ff)
    
    group.addKnob(nuke.Tab_Knob('Flux_Tab', 'Flux Settings'))
    
    modes = ['Master (EXR)', 'Review (MOV)', 'Temp (JPG)']
    group.addKnob(nuke.Enumeration_Knob('render_mode', 'Render Mode', modes))
    
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

    # Script Ver Up
    k_scr = nuke.PyScript_Knob('script_ver_up', 'Script Version Up (Save As...)', "import smart_write\nsmart_write.script_version_up_wrapper()")
    k_scr.setFlag(nuke.STARTLINE); k_scr.setVisible(False)
    group.addKnob(k_scr)

    # Local Ver
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

    open_code = "import os, sys, subprocess; n=nuke.thisNode(); w=nuke.toNode('Write_Internal'); p=w['file'].evaluate(); f=os.path.dirname(p); os.startfile(f) if sys.platform=='win32' else subprocess.Popen(['open', f]) if sys.platform=='darwin' else subprocess.Popen(['xdg-open', f])"
    group.addKnob(nuke.PyScript_Knob('reveal', 'Open Folder', open_code))

    k_bake = nuke.PyScript_Knob('bake', 'Bake Path (Lock)', "import smart_write\nsmart_write.bake_path(nuke.thisNode())")
    k_bake.setTooltip("Lock the file path to a static string.")
    group.addKnob(k_bake)

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