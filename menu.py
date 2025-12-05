import nuke
import flux_env
import set_defaults # New defaults loader

# ------------------------------------------------------------------------------
# Auto Actions
# ------------------------------------------------------------------------------
# コンテキスト自動判定
nuke.addOnScriptLoad(flux_env.update_env_from_script)

# デフォルト設定の適用 (新規スクリプト時)
nuke.addOnScriptLoad(set_defaults.apply_defaults)

# ------------------------------------------------------------------------------
# 1. Main Menu
# ------------------------------------------------------------------------------
menubar = nuke.menu('Nuke')
m = menubar.addMenu('Flux')

m.addCommand('Project Setup', 
             'import project_setup; project_setup.show_dialog()')

m.addCommand('Make Official', 
             'import make_official; make_official.show_dialog()')

m.addCommand('Flux Loader', 
             'import loader; loader.show_dialog()',
             'shift+r')

m.addSeparator()

m.addCommand('Version Up', 
             'import version_up; version_up.run()')

m.addCommand('Create Flux Write', 
             'import smart_write; smart_write.create_flux_write()')

m.addSeparator()

# --- Sub Menu: Utils ---
utils_menu = m.addMenu('Utils')

utils_menu.addCommand('Absolutize Paths (Env Var)', 
                      'import relative_path; relative_path.convert_to_relative()')

utils_menu.addCommand('Node Inspector', 
                      'import node_inspector; node_inspector.dump_node_info()')

# ------------------------------------------------------------------------------
# 2. Nodes Toolbar
# ------------------------------------------------------------------------------
toolbar = nuke.toolbar("Nodes")
t = toolbar.addMenu('Flux', icon='Write.png') 

t.addCommand('Flux Write', 
             'import smart_write; smart_write.create_flux_write()', 
             'shift+w', 
             icon='Write.png')

t.addCommand('Flux Loader',
             'import loader; loader.show_dialog()',
             icon='Read.png')