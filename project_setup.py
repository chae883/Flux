import nuke
import nukescripts
import config
import flux_env
import os

class FluxProjectSetup(nukescripts.PythonPanel):
    def __init__(self):
        super(FluxProjectSetup, self).__init__('Flux Project Setup')
        
        # --- Section 1: Create / Set Context ---
        self.addKnob(nuke.Text_Knob('header_create', '<b>Create / Set Context</b>'))
        
        self.proj_k = nuke.String_Knob('project_code', 'Project Code')
        self.proj_k.setTooltip("e.g. TMP, MYPROJ")
        self.addKnob(self.proj_k)
        
        self.shot_k = nuke.String_Knob('shot_name', 'Shot Name')
        self.shot_k.setTooltip("e.g. shot_010, sh010")
        self.addKnob(self.shot_k)
        
        self.create_btn = nuke.PyScript_Knob('create_structure', 'Create Folder Structure')
        self.addKnob(self.create_btn)

        self.addKnob(nuke.Text_Knob('div_ctx', ''))

        # --- Section 2: Shot Settings ---
        self.addKnob(nuke.Text_Knob('header_settings', '<b>Shot Settings</b>'))

        self.info_label = nuke.Text_Knob('info_label', '', 'Select a Read Node & Click Get')
        self.addKnob(self.info_label)
        self.addKnob(nuke.Text_Knob('divider0', ''))

        self.get_btn = nuke.PyScript_Knob('get_from_selection', 'Get Settings from Selected Read Node')
        self.get_btn.setFlag(nuke.STARTLINE)
        self.addKnob(self.get_btn)
        self.addKnob(nuke.Text_Knob('divider1', ''))

        # Format
        self.all_formats = nuke.formats()
        fmt_names = [f.name() for f in self.all_formats]
        self.format_menu = nuke.Enumeration_Knob('format_menu', 'Format Template', fmt_names)
        self.format_menu.setTooltip("Select a format to auto-fill Width and Height")
        self.addKnob(self.format_menu)

        self.width_k = nuke.Int_Knob('width', 'Width')
        self.height_k = nuke.Int_Knob('height', 'Height')
        self.addKnob(self.width_k)
        self.addKnob(self.height_k)
        
        # FPS & Range
        self.fps_k = nuke.Double_Knob('fps', 'FPS')
        self.first_frame_k = nuke.Int_Knob('first_frame', 'Frame Start')
        self.last_frame_k = nuke.Int_Knob('last_frame', 'Frame End')
        
        self.addKnob(self.fps_k)
        self.addKnob(self.first_frame_k)
        self.addKnob(self.last_frame_k)
        
        self.addKnob(nuke.Text_Knob('divider2', ''))
        self.apply_btn = nuke.PyScript_Knob('apply', 'APPLY TO PROJECT')
        self.addKnob(self.apply_btn)

        # Set Defaults from Config
        self.set_defaults()

    def set_defaults(self):
        # Auto-fill current context if available
        ctx = flux_env.get_context()
        if ctx['project']: self.proj_k.setValue(ctx['project'])
        else: self.proj_k.setValue(getattr(config, 'DEFAULT_PROJECT', 'TMP'))
        
        if ctx['shot']: self.shot_k.setValue(ctx['shot'])

        # Configから読み込み。万が一変数がない場合は安全なデフォルトを使用
        target_fmt = getattr(config, 'DEFAULT_FORMAT', '4K_DCP')
        def_w = getattr(config, 'DEFAULT_WIDTH', 4096)
        def_h = getattr(config, 'DEFAULT_HEIGHT', 2160)
        def_fps = getattr(config, 'DEFAULT_FPS', 24.0)
        def_start = getattr(config, 'DEFAULT_START', 1001)
        def_end = getattr(config, 'DEFAULT_END', 1100)

        # フォーマット設定
        # 既存リストにあるか確認
        fmt_names = [f.name() for f in self.all_formats]
        if target_fmt in fmt_names:
            self.format_menu.setValue(target_fmt)
        
        self.width_k.setValue(def_w)
        self.height_k.setValue(def_h)
        self.fps_k.setValue(def_fps)
        self.first_frame_k.setValue(def_start)
        self.last_frame_k.setValue(def_end)

    def knobChanged(self, knob):
        if knob == self.create_btn:
            self.run_create_structure()
            
        if knob == self.format_menu:
            selected_name = self.format_menu.value()
            for f in self.all_formats:
                if f.name() == selected_name:
                    self.width_k.setValue(f.width())
                    self.height_k.setValue(f.height())
                    break

        if knob == self.get_btn:
            try:
                node = nuke.selectedNode()
                if node.Class() == 'Read':
                    w = node.width()
                    h = node.height()
                    self.width_k.setValue(w)
                    self.height_k.setValue(h)
                    
                    node_format = node.format()
                    if node_format:
                        self.format_menu.setValue(node_format.name())
                    
                    meta = node.metadata()
                    fps_val = 24.0
                    if meta and 'input/frame_rate' in meta:
                        fps_val = float(meta['input/frame_rate'])
                    self.fps_k.setValue(fps_val)
                    
                    self.first_frame_k.setValue(node['first'].value())
                    self.last_frame_k.setValue(node['last'].value())
                    
                    self.info_label.setValue(f"Source: {node.name()} | {w}x{h}")
                else:
                    self.info_label.setValue("Error: Select a READ node.")
            except Exception as e:
                self.info_label.setValue(f"Error: {e}")

        if knob == self.apply_btn:
            self.run_apply_settings()

    def run_create_structure(self):
        proj = self.proj_k.value()
        shot = self.shot_k.value()
        
        if not proj or not shot:
            nuke.message("Please enter both Project and Shot names.")
            return

        try:
            shot_path = flux_env.create_project_structure(proj, shot)
            flux_env.set_global_context(project=proj, shot=shot)
            
            msg = f"Created Folder Structure:\n{shot_path}\n\n"
            msg += "Current Session Context Updated."
            nuke.message(msg)
            
            # Save the script to the new location?
            # Let's ask.
            script_dir = config.normalize_path(os.path.join(shot_path, 'scripts', 'work'))
            if not os.path.exists(script_dir): os.makedirs(script_dir)
            
            script_name = f"{shot}_v001.nk"
            script_full_path = config.normalize_path(os.path.join(script_dir, script_name))
            
            if nuke.root().name() == 'Root' or 'Unsaved' in nuke.root().name():
                if nuke.ask(f"Save current empty script as:\n{script_full_path}?"):
                    nuke.scriptSaveAs(script_full_path)
            
        except Exception as e:
            nuke.message(f"Failed to create structure:\n{e}")

    def run_apply_settings(self):
        try:
            root = nuke.root()
            w = int(self.width_k.value())
            h = int(self.height_k.value())
            selected_fmt_name = self.format_menu.value()
            
            # フォーマット設定
            match_found = False
            for f in self.all_formats:
                if f.name() == selected_fmt_name and f.width() == w and f.height() == h:
                    match_found = True
                    break
            
            if match_found:
                    root['format'].setValue(selected_fmt_name)
            else:
                # カスタムフォーマット作成
                new_format_str = f"{w} {h} Flux_Project"
                nuke.addFormat(new_format_str)
                root['format'].setValue('Flux_Project')
            
            root['fps'].setValue(self.fps_k.value())
            
            start = int(self.first_frame_k.value())
            end = int(self.last_frame_k.value())
            root['first_frame'].setValue(start)
            root['last_frame'].setValue(end)
            root['lock_range'].setValue(True)
            
            # OCIO設定 (Configから)
            ocio_conf = getattr(config, 'DEFAULT_OCIO_CONFIG', '')
            if ocio_conf:
                try:
                    # colorManagementをOCIOに
                    root['colorManagement'].setValue('OCIO')
                except:
                    pass 
            
            nuke.frame(start)
            self.close()
        except Exception as e:
            nuke.message(f"Apply Failed:\n{e}")

def show_dialog():
    FluxProjectSetup().show()