import nuke
import nukescripts
import os
import re
import json
import config
import flux_env

CACHE_FILE_NAME = "flux_assets.json"

class FluxLoader(nukescripts.PythonPanel):
    def __init__(self):
        super(FluxLoader, self).__init__('Flux Loader')
        
        ctx = flux_env.get_context()
        self.shot_root = ""
        if ctx['project'] and ctx['shot']:
            self.shot_root = config.normalize_path(os.path.join(ctx['root'], config.DEFAULT_CONTEXT, ctx['project'], ctx['shot']))
        
        if not os.path.exists(self.shot_root):
             self.shot_root = self.determine_shot_root_fallback()

        display_path = self.shot_root if self.shot_root else "Unknown"
        self.addKnob(nuke.Text_Knob('path_info', 'Shot Path:', display_path))
        self.addKnob(nuke.Text_Knob('div1', ''))

        self.categories = [f for f in config.FOLDER_STRUCTURE if f != 'scripts']
        self.cat_menu = nuke.Enumeration_Knob('category', 'Category', self.categories)
        self.addKnob(self.cat_menu)

        self.asset_menu = nuke.Enumeration_Knob('assets', 'Available Assets', [])
        self.addKnob(self.asset_menu)

        self.refresh_btn = nuke.PyScript_Knob('refresh', 'Force Refresh (Scan Disk)')
        self.refresh_btn.clearFlag(nuke.STARTLINE)
        self.addKnob(self.refresh_btn)
        
        self.load_btn = nuke.PyScript_Knob('load', 'LOAD AS READ NODE')
        self.addKnob(self.load_btn)

        self.scanned_data = {} 
        self.load_from_cache_or_scan()

    def determine_shot_root_fallback(self):
        script_path = nuke.root().name()
        if script_path == 'Root': return None
        return config.normalize_path(os.path.dirname(os.path.dirname(script_path)))

    def get_cache_path(self):
        if self.shot_root:
            return os.path.join(self.shot_root, CACHE_FILE_NAME)
        return None

    def load_from_cache_or_scan(self):
        cache_path = self.get_cache_path()
        if cache_path and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    self.scanned_data = data
                    print(f"[Flux Loader] Loaded assets from cache: {cache_path}")
                    self.update_asset_list()
                    return
            except Exception as e:
                print(f"[Flux Error] Failed to load cache: {e}")
        
        self.scan_disk()

    def scan_disk(self):
        if not self.shot_root or not os.path.exists(self.shot_root):
            self.scanned_data = {}
            return

        print("[Flux Loader] Scanning disk...")
        for cat in self.categories:
            search_path = os.path.join(self.shot_root, cat)
            items = []
            if os.path.exists(search_path):
                try:
                    root_files = nuke.getFileNameList(search_path) or []
                    for f in root_files:
                        full_p = os.path.join(search_path, f)
                        if os.path.isdir(full_p):
                            sub_files = nuke.getFileNameList(full_p) or []
                            for sub in sub_files:
                                items.append(f"{f}/{sub}")
                        else:
                            items.append(f)
                except Exception as e:
                    print(f"[Flux Error] Scan failed for {search_path}: {e}")
            self.scanned_data[cat] = sorted(items)
        
        cache_path = self.get_cache_path()
        if cache_path:
            try:
                with open(cache_path, 'w') as f:
                    json.dump(self.scanned_data, f, indent=4)
                print(f"[Flux Loader] Cache saved to: {cache_path}")
            except Exception as e:
                print(f"[Flux Error] Could not save cache: {e}")

        self.update_asset_list()

    def update_asset_list(self):
        current_cat = self.cat_menu.value()
        items = self.scanned_data.get(current_cat, [])
        if not items: items = ["(No Assets Found)"]
        self.asset_menu.setValues(items)
        self.asset_menu.setValue(0)

    def knobChanged(self, knob):
        if knob == self.cat_menu: self.update_asset_list()
        if knob == self.refresh_btn: self.scan_disk()
        if knob == self.load_btn: self.create_read_node()

    def create_read_node(self):
        if not self.shot_root:
            nuke.message("Error: Script must be saved in a proper project structure first.")
            return
        cat = self.cat_menu.value()
        asset_str = self.asset_menu.value()
        if asset_str == "(No Assets Found)": return

        match = re.match(r'^(.*?)(\s+(\d+-\d+))?$', asset_str)
        if not match: return
        rel_path = match.group(1) 
        range_str = match.group(3)
        full_path = config.normalize_path(os.path.join(self.shot_root, cat, rel_path))
        
        r = nuke.createNode('Read')
        r['file'].fromUserText(full_path)
        
        if range_str:
            try:
                start, end = map(int, range_str.split('-'))
                r['first'].setValue(start)
                r['last'].setValue(end)
                r['origfirst'].setValue(start)
                r['origlast'].setValue(end)
            except Exception as e:
                print(f"[Flux Warning] Frame range parse failed: {e}")

        ext = os.path.splitext(rel_path)[1].lower()
        cs_map = config.LOADER_COLORSPACE_MAP
        if ext in cs_map:
            try: r['colorspace'].setValue(cs_map[ext])
            except Exception as e: print(f"[Flux Warning] Colorspace set failed: {e}")

        if config.LOADER_DISABLE_POSTAGE_STAMP:
            r['postage_stamp'].setValue(False)

        for n in nuke.selectedNodes(): n.setSelected(False)
        r.setSelected(True)

def show_dialog():
    FluxLoader().show()