import bpy
from .ai_operator import AISceneOrganizerOperator
from .preferences import AISceneOrganizerPreferences
from .ui import menu_func, draw_progress_bar, register_properties, unregister_properties, setup_logging

bl_info = {
    "name": "AI Scene Organizer Pro",
    "blender": (4, 3, 2),
    "category": "Object",
    "version": (1, 8, 0),
    "author": "Nael",
    "description": "Organizes scenes using AI with deep hierarchical analysis",
    "location": "View3D > UI > AI Scene Organizer",
    "doc_url": "",
    "tracker_url": "",
    "warning": "",
}

def register():
    try:
        # Register the preferences class first
        bpy.utils.register_class(AISceneOrganizerPreferences)
        
        # Then register other components
        bpy.utils.register_class(AISceneOrganizerOperator)
        
        register_properties()
        setup_logging()
        
        # Register menu
        bpy.types.VIEW3D_MT_object.append(menu_func)
        
    except Exception as e:
        print(f"Error registering AI Scene Organizer: {str(e)}")
        raise

def unregister():
    try:
        # Unregister in reverse order
        bpy.types.VIEW3D_MT_object.remove(menu_func)
        
        unregister_properties()
        
        bpy.utils.unregister_class(AISceneOrganizerOperator)
        bpy.utils.unregister_class(AISceneOrganizerPreferences)
        
    except Exception as e:
        print(f"Error unregistering AI Scene Organizer: {str(e)}")
        raise

if __name__ == "__main__":
    register()