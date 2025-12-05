import nuke
import flux_env
import set_defaults

# Auto Actions
nuke.addOnScriptLoad(flux_env.update_env_from_script)
nuke.addOnScriptLoad(set_defaults.apply_defaults)

# Main Menu
menubar = nuke.menu('Nuke')
m = menubar.addMenu('Flux')

m.addCommand('Project Setup', 'import project_setup; project_setup.show_dialog()')
m.addCommand('Make Official', 'import make_official; make_official.show_dialog()')
m.addCommand('Flux Loader', 'import loader; loader.show_dialog()', 'shift+r')
m.addSeparator()
m.addCommand('Version Up', 'import version_up; version_up.run()')
m.addCommand('Publish Script', 'import publisher; publisher.publish_current_script()', 'shift+p')
m.addCommand('Create Flux Write', 'import smart_write; smart_write.create_flux_write()')
m.addSeparator()

utils = m.addMenu('Utils')
utils.addCommand('Absolutize Paths (Env Var)', 'import resolve_path; resolve_path.convert_to_env_absolute()')
utils.addCommand('Node Inspector', 'import node_inspector; node_inspector.dump_node_info()')

# Toolbar
toolbar = nuke.toolbar("Nodes")
t = toolbar.addMenu('Flux', icon='Write.png') 
t.addCommand('Flux Write', 'import smart_write; smart_write.create_flux_write()', 'shift+w', icon='Write.png')
t.addCommand('Flux Loader', 'import loader; loader.show_dialog()', icon='Read.png')