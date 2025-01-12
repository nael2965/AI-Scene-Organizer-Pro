# ai_organizer/preferences.py
import bpy

class AISceneOrganizerPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    ai_organizer_api_key: bpy.props.StringProperty(
        name="API Key",
        description="Enter your Google Gemini API key",
        default=""
    )
    
    ai_organizer_api_url: bpy.props.StringProperty(
        name="API URL",
        description="Enter your Google Gemini API URL",
        default="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    )
    
    ai_organizer_debug_level: bpy.props.EnumProperty(
        name="Debug Level",
        description="Set the level of debug logging",
        items=[
            ('DEBUG', "Debug", "Detailed information, typically of interest only when diagnosing problems"),
            ('INFO', "Info", "Confirmation that things are working as expected"),
            ('WARNING', "Warning", "An indication that something unexpected happened, or indicative of some problem in the near future"),
            ('ERROR', "Error", "Due to a more serious problem, the software has not been able to perform some function"),
            ('CRITICAL', "Critical", "A very serious error, the program itself may be unable to continue running")
        ],
        default='INFO'
    )
    
    ai_organizer_log_to_file: bpy.props.BoolProperty(
        name="Log to File",
        description="Enable logging to a file",
        default=False
    )
    
    ai_organizer_log_path: bpy.props.StringProperty(
        name="Log File Path",
        description="Path to the log file",
        subtype='FILE_PATH',
        default=""
    )
    
    ai_organizer_save_response: bpy.props.BoolProperty(
        name="Save AI Response",
        description="Enable saving AI response to a file",
        default=False
    )
    
    ai_organizer_response_path: bpy.props.StringProperty(
        name="Response File Path",
        description="Path to save the AI response",
        subtype='FILE_PATH',
        default=""
    )
    
    default_api_url : str = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


    def draw(self, context):
        layout = self.layout
        layout.prop(self, "ai_organizer_api_key")
        layout.prop(self, "ai_organizer_api_url")
        layout.prop(self, "ai_organizer_debug_level")
        layout.prop(self, "ai_organizer_log_to_file")
        if self.ai_organizer_log_to_file:
             layout.prop(self, "ai_organizer_log_path")
        layout.prop(self, "ai_organizer_save_response")
        if self.ai_organizer_save_response:
            layout.prop(self, "ai_organizer_response_path")