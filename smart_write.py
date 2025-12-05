import nuke
import os
import platform
import re
import datetime
import config
import validator
import flux_env
import traceback # エラー詳細表示用

# ------------------------------------------------------------------------------
# PATH CALCULATION (Runtime)
# ------------------------------------------------------------------------------

def get_write_path(node=None):
    """
    Writeノードのファイルパスを計算して返す関数。
    """
    if node is None:
        try:
            node = nuke.thisNode()
            if node.name() == 'Write_Internal':
                node = node.parent()
        except:
            return ""

    if not os.environ.get('FLUX_PROJECT'):
        flux_env.update_env_from_script()

    root = os.environ.get('FLUX_ROOT', config.BASE_ROOT).replace('\\', '/')
    project = os.environ.get('FLUX_PROJECT', 'Unknown')
    shot = os.environ.get('FLUX_SHOT', 'Unknown')
    
    if project == 'Unknown' or shot == 'Unknown':
        return f"{root}/_UNSAVED_/{shot}/renders/unknown.exr"

    try:
        mode = node['render_mode'].value()
        raw_cat = node['render_variant'].value()
        raw_lbl = node['render_label'].value()
        use_local_ver = node['use_local_version'].value()
        local_ver_int = int(node['local_version'].value())
    except Exception as e:
        # TD Feedback: エラーを握りつぶさず出力する
        print(f"[Flux Error] Failed to get knob values in get_write_path: {e}")
        return ""

    cat_str = 'elm' if raw_cat == 'element' else ('' if raw_cat == '(Main)' else raw_cat)
    lbl_str = sanitize_text(raw_lbl)
    ver_str = f"v{local_ver_int:03d}" if use_local_ver else ""
    
    parts = [shot]
    if cat_str: parts.append(cat_str)
    if lbl_str: parts.append(lbl_str)
    if ver_str: parts.append(ver_str)
    
    filename_base = "_".join(parts)
    user_context = config.DEFAULT_CONTEXT 
    shot_path = f"{root}/{user_context}/{project}/{shot}"

    path = ""
    if mode == 'Master (EXR)':
        ext = "exr"
        path = f"{shot_path}/renders/{filename_base}/{filename_base}.%04d.{ext}"
    elif mode == 'Review (MOV)':
        ext = "mov"
        path = f"{shot_path}/renders/dailies/{filename_base}.{ext}"
    elif mode == 'Temp (JPG)':
        ext = "jpg"
        temp_root = config.TEMP_WINDOWS if platform.system() == 'Windows' else config.TEMP_LINUX
        path = f"{temp_root}/nuke_temp/{project}/{shot}/{filename_base}.%04d.{ext}"

    return path

def sanitize_text(text):
    if not text: return ""
    return re.sub(r'[^a-zA-Z0-9_\-]', '', text)

# ------------------------------------------------------------------------------
# UI UPDATE & SETUP
# ------------------------------------------------------------------------------

def update_flux_write(node=None):
    if node is None:
        try: node = nuke.thisNode()
        except: return

    with node:
        w = nuke.toNode('Write_Internal')
        if w:
            current_file = w['file'].value()
            target_expr = "[python {smart_write.get_write_path()}]"
            if current_file != target_expr:
                w['file'].setValue(target_expr)

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
                full_path = get_write_path(node)
                filename = os.path.basename(full_path) if full_path else "Unknown"
                burn['message'].setValue(f"{filename} | Frame: [frame]")
            else:
                burn['disable'].setValue(True)

        apply_format_settings(node, w, mode)
        
        if 'render_info' in node.knobs():
            full_path = get_write_path(node)
            node['render_info'].setValue(f"Target: {os.path.basename(full_path) if full_path else '---'}")

    except Exception as e:
        # TD Feedback: UI更新エラーも出力する
        print(f"[Flux Error] update_flux_write failed: {e}")
        # traceback.print_exc() # デバッグ時はこれも有効

def apply_format_settings(node, w, mode):
    root_working = nuke.root()['workingSpaceLUT'].value() 
    def set_cs(target, keywords=[]):
        try:
            if target and "color_picking" not in target:
                w['colorspace'].setValue(target)
                return
        except: pass # knobがない場合などは無視してOKだが、基本ロジックのエラーは拾うべき
        
        for kw in keywords:
            try:
                for cs in w['colorspace'].values():
                    if "color_picking" in cs.lower(): continue
                    if kw.lower() in cs.lower():
                        w['colorspace'].setValue(cs)
                        return
            except Exception as e:
                print(f"[Flux Warning] Colorspace matching failed: {e}")

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
        except Exception as e:
             print(f"[Flux Warning] MOV codec setup failed: {e}")
             
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
    except Exception as e:
        print(f"[Flux Error] Auto-increment failed: {e}")

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
        except ImportError:
            print("[Flux Warning] Notification module not found.")
        except Exception as e:
            print(f"[Flux Warning] Notification failed: {e}")

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
    except Exception as e: nuke.message(f"Version up script error: {e}")

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

    open_code = "import os, sys, subprocess; n=nuke.thisNode(); w=nuke.toNode('Write_Internal'); p=w['file'].evaluate(); f=os.path.dirname(p); os.startfile(f) if sys.platform=='win32' else subprocess.Popen(['open', f]) if sys.platform=='darwin' else subprocess.Popen(['xdg-open', f])"
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

    # TD Feedback: コールバックでもエラーを握りつぶさない
    # ただし、ロード時の大量エラーを防ぐため、ImportErrorのみpassし、他はprintする
    group['knobChanged'].setValue("try:\n import smart_write\n smart_write.update_flux_write()\nexcept ImportError: pass\nexcept Exception as e: print(e)")
    update_flux_write(group)