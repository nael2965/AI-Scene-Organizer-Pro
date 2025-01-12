import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty
import multiprocessing
import os
from pathlib import Path

def get_prefs():
    return bpy.context.preferences.addons["ai_organizer"].preferences

class AISceneOrganizerPreferences(bpy.types.AddonPreferences):
    bl_idname = "ai_organizer"  # Package name
    
    # API Settings
    api_key: StringProperty(
        name="API Key",
        description="Enter your Google Gemini API key",
        default=""
    )
    
    api_url: StringProperty(
        name="API URL",
        description="Enter your Google Gemini API URL",
        default="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    )
    
    # Debug Settings
    debug_level: EnumProperty(
        name="Debug Level",
        description="Set the level of debug logging",
        items=[
            ('DEBUG', "Debug", "Detailed information for diagnosing problems"),
            ('INFO', "Info", "Confirmation that things are working as expected"),
            ('WARNING', "Warning", "Indication of potential problems"),
            ('ERROR', "Error", "Serious problems"),
            ('CRITICAL', "Critical", "Very serious errors")
        ],
        default='INFO'
    )
    
    enabled: BoolProperty(
        name="Enabled",
        description="Enable/Disable the add-on",
        default=True
    )
    
    log_to_file: BoolProperty(
        name="Log to File",
        description="Enable logging to a file",
        default=False
    )
    
    log_path: StringProperty(
        name="Log File Path",
        description="Path to the log file",
        subtype='FILE_PATH',
        default=""
    )
    
    # Response Settings
    save_response: BoolProperty(
        name="Save AI Response",
        description="Enable saving AI response to a file",
        default=False
    )
    
    response_path: StringProperty(
        name="Response File Path", 
        description="Path to save the AI response",
        subtype='FILE_PATH',
        default=""
    )

    def draw(self, context):
        layout = self.layout
        
        # API Settings
        api_box = layout.box()
        api_box.label(text="API Settings")
        col = api_box.column(align=True)
        col.prop(self, "api_key")
        col.prop(self, "api_url")
        
        # Debug Settings
        debug_box = layout.box()
        debug_box.label(text="Debug Settings")
        col = debug_box.column(align=True)
        col.prop(self, "debug_level")
        col.prop(self, "enabled")
        col.separator()
        col.prop(self, "log_to_file")
        if self.log_to_file:
            col.prop(self, "log_path")
            
        # Response Settings  
        response_box = layout.box()
        response_box.label(text="AI Response Settings")
        col = response_box.column(align=True)
        col.prop(self, "save_response")
        if self.save_response:
            col.prop(self, "response_path")