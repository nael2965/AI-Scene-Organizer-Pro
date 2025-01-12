import bpy
import sys
import os
from datetime import datetime
from pathlib import Path

from .ai_operator import AISceneOrganizerOperator
from .preferences import AISceneOrganizerPreferences
from .utils import logger, setup_logging
from .ui import menu_func, draw_progress_bar, register_properties, unregister_properties

bl_info = {
    "name": "AI Scene Organizer Pro",
    "blender": (4, 3, 2),
    "category": "Object",
    "version": (1, 8, 0),
    "author": "Nael",
    "description": "Advanced AI-powered scene organization system with hierarchical analysis",
    "location": "View3D > Object Menu > AI Scene Organizer",
    "doc_url": "",
    "tracker_url": "",
    "warning": "",
}

def initialize_logging(preferences):
    """Initialize and configure the logging system"""
    try:
        setup_logging(preferences)
        logger.info(f"AI Scene Organizer {'.'.join(map(str, bl_info['version']))} initialization started")
        return True
    except Exception as e:
        print(f"Error initializing logging system: {e}")
        return False

def initialize_workspace(preferences):
    """Set up required directories and workspace"""
    try:
        # Create log directory
        if preferences.log_to_file and preferences.log_path:
            Path(preferences.log_path).mkdir(parents=True, exist_ok=True)
            
        # Create response directory
        if preferences.save_response and preferences.response_path:
            Path(preferences.response_path).mkdir(parents=True, exist_ok=True)
            
        return True
    except Exception as e:
        print(f"Workspace initialization failed: {e}")  # Use print since logger might not be ready
        return False

def validate_environment():
    """Validate the operating environment and dependencies"""
    try:
        # Verify Blender version compatibility
        version = bpy.app.version
        if version < bl_info["blender"]:
            raise Exception(f"Requires Blender {'.'.join(map(str, bl_info['blender']))} or newer")

        # Verify required Python modules
        required_modules = ['requests', 'json']
        missing_modules = [module for module in required_modules 
                         if module not in sys.modules]
        
        if missing_modules:
            raise Exception(f"Missing required modules: {', '.join(missing_modules)}")

        return True
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False

def write_startup_log(preferences):
    """Record startup information in the log"""
    try:
        logger.info("=== AI Scene Organizer Startup Information ===")
        logger.info(f"Version: {'.'.join(map(str, bl_info['version']))}")
        logger.info(f"Blender Version: {'.'.join(map(str, bpy.app.version))}")
        logger.info(f"Debug Level: {preferences.debug_level}")
        logger.info(f"File Logging: {'Enabled' if preferences.log_to_file else 'Disabled'}")
        logger.info(f"Response Saving: {'Enabled' if preferences.save_response else 'Disabled'}")
        logger.info("=========================================")
    except Exception as e:
        logger.error(f"Failed to write startup log: {e}")

def register():
    try:
        # 기본 클래스들 등록
        bpy.utils.register_class(AISceneOrganizerPreferences)
        bpy.utils.register_class(AISceneOrganizerOperator)
        
        # UI와 프로퍼티 등록
        register_properties()
        bpy.types.VIEW3D_MT_object.append(menu_func)
        
        # 설정이 있다면 로깅 시스템 초기화
        addon_prefs = bpy.context.preferences.addons.get("ai_organizer")
        if addon_prefs:
            initialize_workspace(addon_prefs.preferences)
            setup_logging(addon_prefs.preferences)
        
        print("AI Scene Organizer Pro successfully registered")
        
    except Exception as e:
        print(f"Registration failed: {e}")
        if 'addon_prefs' in locals():
            unregister()
        raise

def unregister():
    """Unregister the addon and clean up"""
    try:
        logger.info("Starting addon unregistration")
        
        # Unregister UI elements
        bpy.types.VIEW3D_MT_object.remove(menu_func)
        unregister_properties()
        
        # Unregister classes
        bpy.utils.unregister_class(AISceneOrganizerOperator)
        
        # Clean up logging
        for handler in logger._logger.handlers[:]:
            logger._logger.removeHandler(handler)
        
        # Unregister preferences last
        bpy.utils.unregister_class(AISceneOrganizerPreferences)
        
        logger.info("AI Scene Organizer successfully unregistered")
        
    except Exception as e:
        print(f"Error during unregistration: {e}")
        raise

if __name__ == "__main__":
    register()