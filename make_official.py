import nuke
import nukescripts
import os
import subprocess
import config
import flux_env

class FluxMakeOfficial(nukescripts.PythonPanel):
    def __init__(self):
        super(FluxMakeOfficial, self).__init__('Flux Make Official')
        
        self.base_root = config.BASE_ROOT
        self.ap_exe_path = config.ANCHORPOINT_PATH
        
        self.addKnob(nuke.Text_Knob('info', '', 'Define Shot Structure'))
        
        self.context_k = nuke.String_Knob('context', 'Context/User')
        self.context_k.setValue(config.DEFAULT_CONTEXT)
        self.addKnob(self.context_k)
        
        self.proj_k = nuke.String_Knob('project', 'Project Code (3 chars)')
        self.proj_k.setValue(config.DEFAULT_PROJECT)
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
        
        self.open_ap_k = nuke.Boolean_Knob('open_ap', 'Open Project in Anchorpoint')
        self.open_ap_k.setValue(True)
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
        project_root = os.path.join(self.base_root, context, project)
        shot_dir = os.path.join(project_root, shot_name)
        
        # TD Update: Save into 'scripts/work' by default
        script_dir = os.path.join(shot_dir, 'scripts', 'work')
        
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

        sub_folders = config.FOLDER_STRUCTURE
        
        try:
            for sub in sub_folders:
                path_to_make = os.path.join(shot_dir, sub)
                if not os.path.exists(path_to_make):
                    os.makedirs(path_to_make)
            
            # Ensure the specific work script dir exists (it might be nested in the config structure)
            if not os.path.exists(script_dir):
                os.makedirs(script_dir)

            save_path = full_path.replace('\\', '/')
            if os.path.exists(save_path):
                if not nuke.ask(f"File already exists:\n{save_path}\n\nOverwrite?"):
                    return
            
            nuke.scriptSaveAs(save_path)
            
            flux_env.update_env_from_script()
            
            if self.open_ap_k.value():
                self.launch_anchorpoint(project_root)

            nuke.message(f"Shot Initialized!\nSaved to: {save_path}")
            self.close()
            
        except Exception as e:
            nuke.message(f"Error:\n{e}")

    def launch_anchorpoint(self, target_path):
        target_path = os.path.abspath(target_path)
        exe_path = os.path.abspath(self.ap_exe_path)

        if os.path.exists(exe_path):
            try:
                subprocess.Popen([exe_path, target_path])
                print(f"Flux: Opening Anchorpoint at {target_path}")
            except Exception as e:
                print(f"Flux: Failed to launch Anchorpoint. {e}")
        else:
            print(f"Flux Warning: Anchorpoint executable not found at {exe_path}")
            
def show_dialog():
    panel = FluxMakeOfficial()
    panel.show()