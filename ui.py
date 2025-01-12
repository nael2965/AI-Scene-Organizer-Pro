# ai_organizer/ui.py
import bpy
import logging
from .utils import logger

def menu_func(self, context):
    self.layout.operator("object.ai_scene_organizer")

def draw_progress_bar(self, context):
    layout = self.layout
    scene = context.scene
    if 'ai_organizer_progress' in scene:
        layout.prop(scene, "ai_organizer_progress", text="Progress", slider=True)
        
# --- Properties ---
def register_properties():
    bpy.types.Scene.ai_organizer_progress = bpy.props.IntProperty(
        name="AI Organizer Progress",
        description="AI Organizer progress percentage",
        default=0,
        min=0,
        max=100
    )


def unregister_properties():
    del bpy.types.Scene.ai_organizer_progress
    
    
def setup_logging():
    prefs = bpy.context.preferences.addons[__name__].preferences
    log_level = getattr(logging, prefs.ai_organizer_debug_level)
    if prefs.ai_organizer_log_to_file and prefs.ai_organizer_log_path:
       logging.basicConfig(filename=prefs.ai_organizer_log_path, level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    global logger
    logger = logging.getLogger(__name__)