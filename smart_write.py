import nuke
import os
import platform
import re
import datetime
import config  # Updated config loader

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------

def get_script_root_name():
    root_name = nuke.root().name()
    if root_name == 'Root':
        return None
    return os.path.splitext(os.path.basename(root_name))[0]

def sanitize_text(text):
    if not text:
        return ""
    safe_text = re.sub(r'[^a-zA-Z0-9_\-]', '', text)
    return safe_text

# Local Version Button Actions
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

# Script Version Up Action
def script_version_up_wrapper():
    try:
        import version_up
        version_up.run()
    except ImportError:
        nuke.message("Error: 'version_up.py' not found.")
    except Exception as e:
        nuke.message(f"Error:\n{e}")

# ------------------------------------------------------------------------------
# CORE LOGIC
# ------------------------------------------------------------------------------

def update_flux_write(node=None):
    if node is None:
        try:
            node = nuke.thisNode()
        except:
            return

    # Trigger Guard
    trigger_knobs = [
        'render_mode', 'render_variant', 'render_label', 
        'use_local_version', 'local_version', 'showPanel',
        'use_burnin'
    ]
    try:
        k = nuke.thisKnob()
        if k and k.name() not in trigger_knobs: 
            return
    except:
        pass

    script_name = get_script_root_name()
    if not script_name:
        node['label'].setValue("⚠️ SCRIPT NOT SAVED ⚠️")
        return

    # --- Fetch Values ---
    try:
        mode = node['render_mode'].value()      
        raw_cat = node['render_variant'].value()
        raw_lbl = node['render_label'].value()
        use_local_ver = node['use_local_version'].value()
        local_ver_int = int(node['local_version'].value())
        use_burnin = node['use_burnin'].value()
    except ValueError:
        return 

    # --- Dynamic UI Control ---
    is_main = (raw_cat == '(Main)')
    k_grp_local = [
        node.knob('use_local_version'), node.knob('ver_down'), 
        node.knob('local_version'), node.knob('ver_up')
    ]
    k_btn_script = node.knob('script_ver_up')
    k_render = node.knob('render_now')
    k_burnin = node.knob('use_burnin')

    if is_main:
        for k in k_grp_local: k.setVisible(False)
        k_btn_script.setVisible(True)
        k_render.setLabel("Render (Main)")
        use_local_ver = False 
    else:
        for k in k_grp_local: k.setVisible(True)
        k_btn_script.setVisible(False)
        if use_local_ver:
            k_render.setLabel("Render (Auto-Inc)")
        else:
            k_render.setLabel("Render (Current)")

    is_mov = (mode == 'Review (MOV)')
    k_burnin.setVisible(is_mov)

    # --- Internal Nodes ---
    with node:
        w = nuke.toNode('Write_Internal')
        burn = nuke.toNode('BurnIn_Internal')
    
    if not w or not burn: return 

    # --- Naming Logic ---
    category_str = ""
    if raw_cat != '(Main)':
        if raw_cat == 'element': category_str = 'elm'
        else: category_str = raw_cat

    label_str = sanitize_text(raw_lbl)

    parts = []
    if category_str: parts.append(category_str)
    if label_str:    parts.append(label_str)
    
    version_suffix = ""
    if use_local_ver:
        version_suffix = f"_v{local_ver_int:03d}"

    full_suffix_elements = []
    if parts:
        full_suffix_elements.extend(parts)
    
    mid_suffix = "_".join(full_suffix_elements)
    final_suffix_str = ""
    if mid_suffix: final_suffix_str += f"_{mid_suffix}"
    if version_suffix: final_suffix_str += version_suffix

    base_name_tcl = "[file rootname [file tail [value root.name]]]"
    final_name_str = f"{base_name_tcl}{final_suffix_str}"

    # --- Directories ---
    render_dir = "[file dirname [value root.name]]/../renders"
    
    # ConfigからTempパスを取得
    if platform.system() == 'Windows':
        temp_root = config.TEMP_WINDOWS
    else:
        temp_root = config.TEMP_LINUX

    # --- Burn-in Control ---
    if is_mov and use_burnin:
        burn['disable'].setValue(False)
        msg = f"{final_name_str}  |  Frame: [frame]"
        burn['message'].setValue(msg)
    else:
        burn['disable'].setValue(True)

    # --- Helper Functions ---
    try:
        available_cs = w['colorspace'].values()
    except:
        available_cs = []

    def set_colorspace_smart(target_value, fallback_keywords=[]):
        if target_value:
            try:
                if "color_picking" not in target_value:
                    w['colorspace'].setValue(target_value)
                    return True
            except: pass

        for kw in fallback_keywords:
            for cs_name in available_cs:
                if "color_picking" in cs_name.lower(): continue
                if kw.lower() in cs_name.lower():
                    try: w['colorspace'].setValue(cs_name); return True
                    except: pass
        return False

    def make_label(type_text, color):
        node['tile_color'].setValue(color)
        disp = f"{type_text}\n{script_name}"
        if final_suffix_str: disp += f"\n[{final_suffix_str.lstrip('_')}]"
        node['label'].setValue(disp)

    # --- Root Settings ---
    root = nuke.root()
    root_working = root['workingSpaceLUT'].value() 

    # --------------------------------------------------------------------------
    # 3. APPLY SETTINGS (FROM CONFIG)
    # --------------------------------------------------------------------------

    # === MODE: Master (EXR) ===
    if mode == 'Master (EXR)':
        w['transformType'].setValue('colorspace')
        
        path = f"{render_dir}/{final_name_str}/{final_name_str}.%04d.exr"
        w['file'].setValue(path)
        
        # ConfigからEXR設定を適用
        exr_settings = config.RENDER_EXR
        w['file_type'].setValue('exr')
        w['datatype'].setValue(exr_settings.get('datatype', '32 bit float'))
        w['compression'].setValue(exr_settings.get('compression', 'Zip (1 scanline)'))
        w['metadata'].setValue('all metadata')
        w['views'].setValue('main')
        w['channels'].setValue('rgb')
        
        linear_candidates = ['default', 'scene_linear', 'ACES - ACEScg', 'ACEScg']
        set_colorspace_smart(root_working, linear_candidates)
        
        make_label("EXR (32f)", 0x44aa44ff)

    # === MODE: Review (MOV) ===
    elif mode == 'Review (MOV)':
        w['transformType'].setValue('display')
        
        path = f"{render_dir}/dailies/{final_name_str}.mov"
        w['file'].setValue(path)
        w['file_type'].setValue('mov')
        
        # ConfigからMOV設定を適用
        mov_settings = config.RENDER_MOV
        try:
            w['mov64_codec'].setValue(mov_settings.get('codec', 'appr'))
            w['mov_prores_codec_profile'].setValue(mov_settings.get('prores_profile', 'ProRes 4:4:4:4 XQ 12-bit'))
            w['mov_h264_codec_profile'].setValue(mov_settings.get('h264_profile', 'High 4:2:0 8-bit'))
            w['mov64_quality'].setValue(mov_settings.get('quality', 'High'))
        except: pass
            
        w['views'].setValue('main')
        w['channels'].setValue('rgb')

        try:
            w['ocioDisplay'].setValue('sRGB - Display')
            w['ocioView'].setValue('ACES 1.0 - SDR Video')
        except:
            try:
                w['ocioDisplay'].setValue('sRGB')
                w['ocioView'].setValue('sRGB')
            except: pass

        make_label("MOV (Review)", 0x4488aaff)

    # === MODE: Temp (JPG) ===
    elif mode == 'Temp (JPG)':
        w['transformType'].setValue('display')
        
        path = f"{temp_root}/nuke_temp/{script_name}/{script_name}{final_suffix_str}.%04d.jpg"
        w['file'].setValue(path)
        w['file_type'].setValue('jpeg')
        
        # ConfigからJPG設定を適用
        jpg_settings = config.RENDER_JPG
        try:
            w['_jpeg_quality'].setValue(jpg_settings.get('quality', 1.0))
            w['_jpeg_sub_sampling'].setValue(jpg_settings.get('sub_sampling', '4:4:4'))
        except: pass
            
        w['views'].setValue('main')
        w['channels'].setValue('rgb')

        try:
            w['ocioDisplay'].setValue('sRGB - Display')
            w['ocioView'].setValue('ACES 1.0 - SDR Video')
        except:
            pass

        make_label("TEMP (JPG)", 0xaa4444ff)

    # --------------------------------------------------------------------------
    # 4. UPDATE INFO DISPLAY
    # --------------------------------------------------------------------------
    if 'render_info' in node.knobs():
        info_lines = []
        out_path = w['file'].value()
        file_name_disp = os.path.basename(out_path)
        info_lines.append(f"File: {file_name_disp}")
        
        ftype = w['file_type'].value()
        
        if w['transformType'].value() == 'display':
            try:
                cspace = f"{w['ocioDisplay'].value()} / {w['ocioView'].value()}"
            except:
                cspace = "Display Transform"
        else:
            cspace = w['colorspace'].value()
        
        if ftype == 'exr':
            dt = w['datatype'].value()
            comp = w['compression'].value()
            info_lines.append(f"Format: EXR ({dt})")
            info_lines.append(f"Comp: {comp}")
        elif ftype == 'mov':
            codec_disp = "Unknown Codec"
            try:
                codec_fam = w['mov64_codec'].value()
                if codec_fam == 'appr':
                    codec_disp = w['mov_prores_codec_profile'].value()
                elif codec_fam == 'avc1':
                    codec_disp = f"H.264 ({w['mov_h264_codec_profile'].value()})"
                else:
                    codec_disp = codec_fam
            except: pass
            info_lines.append(f"Format: MOV ({codec_disp})")
        elif ftype == 'jpeg':
            qual = w['_jpeg_quality'].value()
            info_lines.append(f"Format: JPEG (Quality {qual})")
            
        info_lines.append(f"Color: {cspace}")
        node['render_info'].setValue("\n".join(info_lines))


# ------------------------------------------------------------------------------
# RENDER ACTION
# ------------------------------------------------------------------------------

def render_with_auto_increment():
    node = nuke.thisNode()
    try:
        raw_cat = node['render_variant'].value()
        is_main = (raw_cat == '(Main)')
        use_local = node['use_local_version'].value()
    except: return

    if is_main: use_local = False

    if not is_main and use_local:
        current_ver = int(node['local_version'].value())
        new_ver = current_ver + 1
        node['local_version'].setValue(new_ver)
        update_flux_write(node)

    first_frame = int(nuke.root().firstFrame())
    last_frame = int(nuke.root().lastFrame())
    
    inp = node.input(0)
    if inp:
        first_frame = int(inp.firstFrame())
        last_frame = int(inp.lastFrame())
        
    try:
        print(f"Flux Render: Frames {first_frame}-{last_frame}")
        
        start_time = datetime.datetime.now()
        
        nuke.execute(node, first_frame, last_frame)
        
        try:
            with node:
                w_internal = nuke.toNode('Write_Internal')
            
            import notification
            notification.show_notification(w_internal, start_time, first_frame, last_frame)
            
        except ImportError:
            print("Flux Warning: notification module not found.")
        except Exception as e:
            print(f"Flux Warning: Notification failed. {e}")

    except RuntimeError as e:
        if "Cancelled" not in str(e):
            nuke.message(f"Render Error:\n{e}")

# ------------------------------------------------------------------------------
# NODE CREATION
# ------------------------------------------------------------------------------

def create_flux_write():
    if not get_script_root_name():
        nuke.message("⚠️ Please Save Script First!\nスクリプトを保存してから実行してください。")
        return

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

    k_label = nuke.String_Knob('render_label', '') 
    k_label.clearFlag(nuke.STARTLINE)
    group.addKnob(k_label)
    
    group.addKnob(nuke.Text_Knob('div1', ''))

    k_burnin = nuke.Boolean_Knob('use_burnin', 'Burn-in Info')
    k_burnin.setTooltip("Add text overlay (Shot Name & Frame) for Review/MOV.")
    k_burnin.setValue(True)
    k_burnin.setFlag(nuke.STARTLINE)
    group.addKnob(k_burnin)

    cmd_ver_up_script = "import smart_write\nsmart_write.script_version_up_wrapper()"
    k_ver_up_script = nuke.PyScript_Knob('script_ver_up', 'Script Version Up (Save As...)', cmd_ver_up_script)
    k_ver_up_script.setFlag(nuke.STARTLINE)
    k_ver_up_script.setVisible(False) 
    group.addKnob(k_ver_up_script)

    k_use_ver = nuke.Boolean_Knob('use_local_version', 'Use Local Version')
    k_use_ver.setFlag(nuke.STARTLINE)
    k_use_ver.setVisible(False)
    group.addKnob(k_use_ver)

    cmd_down = "import smart_write\nsmart_write.local_version_down(nuke.thisNode())"
    k_down = nuke.PyScript_Knob('ver_down', ' - ', cmd_down)
    k_down.clearFlag(nuke.STARTLINE)
    k_down.setVisible(False)
    group.addKnob(k_down)

    k_ver = nuke.Int_Knob('local_version', '')
    k_ver.setValue(1)
    k_ver.clearFlag(nuke.STARTLINE)
    k_ver.setVisible(False)
    group.addKnob(k_ver)

    cmd_up = "import smart_write\nsmart_write.local_version_up(nuke.thisNode())"
    k_up = nuke.PyScript_Knob('ver_up', ' + ', cmd_up)
    k_up.clearFlag(nuke.STARTLINE)
    k_up.setVisible(False)
    group.addKnob(k_up)

    group.addKnob(nuke.Text_Knob('div2', ''))

    cmd_render = "import smart_write\nsmart_write.render_with_auto_increment()"
    k_render = nuke.PyScript_Knob('render_now', 'Render', cmd_render)
    k_render.setFlag(nuke.STARTLINE) 
    group.addKnob(k_render)

    open_code = """
import os, sys, subprocess
n = nuke.thisNode()
with n: w = nuke.toNode('Write_Internal')
path = w['file'].evaluate()
folder = os.path.dirname(path)
if os.path.exists(folder):
    if sys.platform == 'win32': os.startfile(folder)
    elif sys.platform == 'darwin': subprocess.Popen(['open', folder])
    else: subprocess.Popen(['xdg-open', folder])
else: nuke.message("Folder does not exist yet.\\nRender first!")
"""
    k_open = nuke.PyScript_Knob('reveal', 'Open Folder', open_code)
    group.addKnob(k_open)

    group.addKnob(nuke.Text_Knob('div3', '')) 
    k_info = nuke.Text_Knob('render_info', 'Current Settings:')
    k_info.setValue('Initializing...') 
    group.addKnob(k_info)

    with group:
        inp = nuke.createNode('Input')
        
        burn = nuke.createNode('Text2')
        burn.setName('BurnIn_Internal')
        burn['box'].setValue([0, 0, nuke.root().width(), 80])
        burn['xjustify'].setValue('center')
        burn['yjustify'].setValue('bottom')
        burn['global_font_scale'].setValue(0.4)
        burn['enable_background'].setValue(True)
        burn['background_opacity'].setValue(0.6)
        burn['background_border_x'].setValue(2000)
        
        w = nuke.createNode('Write')
        w.setName('Write_Internal')
        w['create_directories'].setValue(True)
        
        out = nuke.createNode('Output')
        
        burn.setInput(0, inp)
        w.setInput(0, burn)
        out.setInput(0, w)

    callback_code = """
try:
    import smart_write
    smart_write.update_flux_write()
except ImportError:
    pass
"""
    group['knobChanged'].setValue(callback_code)
    
    update_flux_write(group)