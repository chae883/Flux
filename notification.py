import nuke
import os
import sys
import platform
import subprocess
import datetime
import requests
import json
import config

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# Import the NEW clean UI class
from ui_notif_panel import Ui_MainWindow

# --- Configuration (From config.py) ---
WEBHOOK_URL = config.WEBHOOK_URL
PLAYER_PATH = config.PLAYER_PATH
FILE_EXPLORER_PATH = config.FILE_EXPLORER_PATH

# --- Notification Logic ---

def send_discord_notification(fields):
    """Builds and sends a GREEN success embed to Discord."""
    if not WEBHOOK_URL:
        print("Flux Notification: No Webhook URL set.")
        return

    embed = {
        "title": "✅ Render Finished!",
        "color": 3066993, # Green
        "fields": fields,
        "footer": {"text": f"Flux Pipeline | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
    }
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Flux Notification Warning: Discord send failed. {e}")

# --- UI Class ---

class FluxNotificationPanel(QMainWindow):
    def __init__(self, write_node, duration_str):
        super(FluxNotificationPanel, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.Write_node = write_node
        
        # --- Window Effect Setup ---
        # Note: Some effects handled in ui_notif_panel.py now (translucency)
        
        self.op_effect = QGraphicsOpacityEffect(self)
        self.op_effect.setOpacity(0.95)
        self.setGraphicsEffect(self.op_effect)
        
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 100))
        self.ui.frame.setGraphicsEffect(self.shadow)
        
        # Center on Screen
        screen = QApplication.primaryScreen().geometry()
        self.move(int(screen.center().x() - self.width()/2.0), int(screen.center().y() - self.height()/2.0))
        
        # Connect Signals
        self.ui.pushButton_close.clicked.connect(self.close)
        self.ui.pushButton_folder.clicked.connect(self.open_render_directory)
        self.ui.pushButton_file.clicked.connect(self.open_render_file)
        self.ui.pushButton_CreateRead.clicked.connect(self.create_read_node)
        
        # Set Data
        script_name = os.path.basename(nuke.root().name())
        self.ui.label_project.setText(script_name)
        self.ui.label_duration.setText(f"Duration: {duration_str}")

    def open_render_directory(self):
        # We need to resolve the path because it might contain [getenv] variables now
        path_raw = nuke.filename(self.Write_node)
        if path_raw:
            path = nuke.tcl('subst', path_raw) # Resolve TCL vars
            dir_path = os.path.dirname(path)
            self.open_explorer(dir_path)

    def open_render_file(self):
        path_raw = nuke.filename(self.Write_node)
        if path_raw:
            path = nuke.tcl('subst', path_raw) # Resolve TCL vars
            self.open_player(path)

    def open_explorer(self, path):
        path = os.path.normpath(path)
        if FILE_EXPLORER_PATH and os.path.exists(FILE_EXPLORER_PATH):
            subprocess.Popen([FILE_EXPLORER_PATH, path])
        elif platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", path])

    def open_player(self, path):
        if PLAYER_PATH and os.path.exists(PLAYER_PATH):
            subprocess.Popen([PLAYER_PATH, path])
        else:
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", path])

    def create_read_node(self):
        file_path_raw = nuke.filename(self.Write_node)
        if not file_path_raw: return

        # For Read node, we prefer the abstract path (farm safe) if possible,
        # but Nuke Read nodes handle [getenv] natively, so passing the raw value is perfect.
        # file_path_raw is already the string from the Write node knob.
        
        read = nuke.createNode("Read")
        read['file'].fromUserText(file_path_raw)
        
        first = int(nuke.root()["first_frame"].getValue())
        last = int(nuke.root()["last_frame"].getValue())
        
        # Check for frame padding symbols in the raw string
        if "%" in file_path_raw or "#" in file_path_raw:
            read['first'].setValue(first)
            read['last'].setValue(last)
            read['origfirst'].setValue(first)
            read['origlast'].setValue(last)
        
        try:
            parent_node = self.Write_node.parent()
            if parent_node and parent_node.Class() == 'Group':
                read.setXpos(parent_node.xpos())
                read.setYpos(parent_node.ypos() + 120)
        except:
            pass
        
        self.close()

_flux_notification_instances = []

def show_notification(write_node, start_time, first_frame, last_frame):
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    duration_s = duration.total_seconds()
    
    hours, remainder = divmod(int(duration_s), 3600)
    minutes, seconds = divmod(int(remainder), 60)
    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
    
    num_frames = (last_frame - first_frame) + 1
    avg_time_str = "N/A"
    if num_frames > 0:
        avg = duration_s / num_frames
        avg_time_str = f"{avg:.2f}s"

    script_name = os.path.basename(nuke.root().name())
    
    # Resolve filename for display in Discord
    render_path_raw = nuke.filename(write_node)
    render_path = nuke.tcl('subst', render_path_raw)
    filename = os.path.basename(render_path)
    
    fields = [
        {"name": "Script", "value": f"`{script_name}`", "inline": False},
        {"name": "File", "value": f"`{filename}`", "inline": False},
        {"name": "Range", "value": f"{first_frame}-{last_frame} ({num_frames}f)", "inline": True},
        {"name": "Duration", "value": time_str, "inline": True},
        {"name": "Avg/Frame", "value": avg_time_str, "inline": True}
    ]
    
    try:
        send_discord_notification(fields)
    except:
        pass

    def _show_ui():
        global _flux_notification_instances
        _flux_notification_instances = [w for w in _flux_notification_instances if w.isVisible()]
        
        window = FluxNotificationPanel(write_node, time_str)
        _flux_notification_instances.append(window)
        
        window.show()
        window.raise_()
        window.activateWindow()

    nuke.executeInMainThread(_show_ui)