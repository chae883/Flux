import nuke
import nukescripts
import os
import subprocess

class FluxMakeOfficial(nukescripts.PythonPanel):
    def __init__(self):
        super(FluxMakeOfficial, self).__init__('Flux Make Official')
        
        # --- 設定エリア --------------------------
        self.base_root = "D:/Studio/WIP"
        
        # Anchorpointの実行ファイルパス (Windowsデフォルト)
        # %LOCALAPPDATA% を自動で展開します
        local_app_data = os.environ.get('LOCALAPPDATA')
        self.ap_exe_path = os.path.join(local_app_data, "Anchorpoint", "Anchorpoint.exe")
        # ----------------------------------------
        
        # --- UI定義 ---
        self.addKnob(nuke.Text_Knob('info', '', 'Define Shot Structure'))
        
        self.context_k = nuke.String_Knob('context', 'Context/User')
        self.context_k.setValue('private')
        self.addKnob(self.context_k)
        
        self.proj_k = nuke.String_Knob('project', 'Project Code (3 chars)')
        self.proj_k.setValue('TMP')
        self.addKnob(self.proj_k)
        
        self.seq_k = nuke.String_Knob('seq', 'Seq (e.g. 101)')
        self.shot_k = nuke.String_Knob('shot', 'Shot (e.g. 010)')
        self.seq_k.clearFlag(nuke.STARTLINE)
        self.shot_k.clearFlag(nuke.STARTLINE)
        self.addKnob(self.seq_k)
        self.addKnob(self.shot_k)
        
        self.addKnob(nuke.Text_Knob('div1', ''))
        
        self.preview_k = nuke.Text_Knob('preview', 'Preview Path:', '')
        self.addKnob(self.preview_k)
        
        self.addKnob(nuke.Text_Knob('div2', ''))
        
        # ★ Anchorpoint連携用チェックボックス
        self.open_ap_k = nuke.Boolean_Knob('open_ap', 'Open Project in Anchorpoint')
        self.open_ap_k.setValue(True) # デフォルトでON
        self.open_ap_k.setFlag(nuke.STARTLINE)
        self.addKnob(self.open_ap_k)

        self.create_btn = nuke.PyScript_Knob('create', 'CREATE & SAVE v001')
        self.addKnob(self.create_btn)

        self.update_preview()

    def knobChanged(self, knob):
        if knob in [self.context_k, self.proj_k, self.seq_k, self.shot_k]:
            self.update_preview()
        if knob == self.create_btn:
            self.execute_creation()

    def get_paths(self):
        context = self.context_k.value()
        project = self.proj_k.value().upper()
        seq = self.seq_k.value()
        shot = self.shot_k.value()
        
        shot_name = f"{project}_{seq}_{shot}"
        
        # Project Root (例: .../TMP) -> Anchorpointで開くのはここ
        project_root = os.path.join(self.base_root, context, project)
        
        # Shot Dir (例: .../TMP/TMP_101_010)
        shot_dir = os.path.join(project_root, shot_name)
        
        script_dir = os.path.join(shot_dir, 'scripts')
        file_name = f"{shot_name}_comp_v001.nk"
        full_path = os.path.join(script_dir, file_name).replace('\\', '/')
        
        return project_root, shot_dir, script_dir, full_path

    def update_preview(self):
        _, _, _, full_path = self.get_paths()
        self.preview_k.setValue(f"<font size=3 color='gray'>{full_path}</font>")

    def execute_creation(self):
        project_root, shot_dir, script_dir, full_path = self.get_paths()
        
        if not self.proj_k.value() or not self.seq_k.value() or not self.shot_k.value():
            nuke.message("Error: Project, Sequence, and Shot are required.")
            return

        sub_folders = ['scripts', 'renders', 'plates', 'ref']
        
        try:
            # フォルダ作成
            for sub in sub_folders:
                path_to_make = os.path.join(shot_dir, sub)
                if not os.path.exists(path_to_make):
                    os.makedirs(path_to_make)
            
            # 保存
            save_path = full_path.replace('\\', '/')
            if os.path.exists(save_path):
                if not nuke.ask(f"File already exists:\n{save_path}\n\nOverwrite?"):
                    return
            
            nuke.scriptSaveAs(save_path)
            
            # ★ Anchorpoint連携処理
            if self.open_ap_k.value():
                self.launch_anchorpoint(project_root)

            nuke.message(f"Shot Initialized!\nSaved to: {save_path}")
            self.close()
            
        except Exception as e:
            nuke.message(f"Error:\n{e}")

    def launch_anchorpoint(self, target_path):
        """Anchorpointを指定したパスで開く"""
        # パス区切り文字の正規化
        target_path = os.path.abspath(target_path)
        exe_path = os.path.abspath(self.ap_exe_path)

        if os.path.exists(exe_path):
            try:
                # subprocessを使って非同期で起動（Nukeをフリーズさせないため）
                # 引数にフォルダパスを渡すと、Anchorpointはその場所を開こうとします
                subprocess.Popen([exe_path, target_path])
                print(f"Flux: Opening Anchorpoint at {target_path}")
            except Exception as e:
                print(f"Flux: Failed to launch Anchorpoint. {e}")
        else:
            print(f"Flux Warning: Anchorpoint executable not found at {exe_path}")
            # エラーで止めず、ログに出すだけに留める
            
def show_dialog():
    panel = FluxMakeOfficial()
    panel.show()