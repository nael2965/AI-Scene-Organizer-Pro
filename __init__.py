# ai_organizer/__init__.py
import bpy
from .operator import AISceneOrganizerOperator
from .preferences import AISceneOrganizerPreferences
from .ui import menu_func, draw_progress_bar, register_properties, unregister_properties, setup_logging

bl_info = {
    "name": "AI Scene Organizer Pro",
    "blender": (4, 3, 2),
    "category": "Object",
    "version": (1, 7),
    "author": "Nael",
    "description": "Organizes scenes using AI with deep hierarchical analysis",
}

def register():
    setup_logging()
    bpy.utils.register_class(AISceneOrganizerPreferences)
    bpy.utils.register_class(AISceneOrganizerOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.STATUSBAR_HT_header.append(draw_progress_bar)
    register_properties()

def unregister():
    bpy.utils.unregister_class(AISceneOrganizerPreferences)
    bpy.utils.unregister_class(AISceneOrganizerOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.types.STATUSBAR_HT_header.remove(draw_progress_bar)
    unregister_properties()

if __name__ == "__main__":
    register()