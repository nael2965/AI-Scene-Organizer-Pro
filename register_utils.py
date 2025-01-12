# register_utils.py
import bpy

def register_specific(bl_info):
    from .preferences import AISceneOrganizerPreferences
    bpy.types.Scene.ai_organizer_progress = bpy.props.IntProperty(
        name="AI Organizer Progress",
        description="AI Organizer progress percentage",
        default=0,
        min=0,
        max=100
    )

def unregister_specific(bl_info):
     if hasattr(bpy.types.Scene, "ai_organizer_progress"):
        del bpy.types.Scene.ai_organizer_progress