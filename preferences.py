import bpy
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    IntProperty,
    FloatProperty
)
import os
from pathlib import Path
from datetime import datetime

class AISceneOrganizerPreferences(bpy.types.AddonPreferences):
    bl_idname = "ai_organizer"

    # API Configuration
    api_key: StringProperty(
        name="API Key",
        description="Google Gemini API authentication key",
        default="",
        subtype='PASSWORD'
    )
    
    api_url: StringProperty(
        name="API URL",
        description="Google Gemini API endpoint URL",
        default="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    )
    
    use_batch_processing: BoolProperty(
        name="Use Batch Processing",
        description="Process large scenes in smaller batches to avoid token limits",
        default=False
    )
    
    batch_size: IntProperty(
        name="Batch Size",
        description="Number of items to process in each batch (recommended: 20-30)",
        default=20,
        min=5,
        max=50,
        soft_min=10,
        soft_max=40
    )

    # Logging Configuration
    debug_level: EnumProperty(
        name="Debug Level",
        description="Set the level of debug information to log",
        items=[
            ('DEBUG', "Debug", "Detailed technical information for debugging"),
            ('INFO', "Info", "General operational information"),
            ('WARNING', "Warning", "Potential issues that might need attention"),
            ('ERROR', "Error", "Serious problems that need immediate attention"),
            ('CRITICAL', "Critical", "Critical failures that prevent operation")
        ],
        default='INFO'
    )
    
    log_to_file: BoolProperty(
        name="Enable File Logging",
        description="Save log messages to a file",
        default=False
    )
    
    log_path: StringProperty(
        name="Log File Location",
        description="Directory where log files will be saved",
        subtype='DIR_PATH',
        default=str(Path.home() / "BlenderAIOrganizer" / "logs")
    )
    
    # Response Management
    save_response: BoolProperty(
        name="Save AI Responses",
        description="Save detailed AI analysis responses for review",
        default=False
    )
    
    response_path: StringProperty(
        name="Response File Location",
        description="Directory where AI response files will be saved",
        subtype='DIR_PATH',
        default=str(Path.home() / "BlenderAIOrganizer" / "responses")
    )

    def draw(self, context):
        layout = self.layout
        
        # API Settings
        api_box = layout.box()
        api_box.label(text="API Configuration", icon='URL')
        api_col = api_box.column()
        api_col.prop(self, "api_key")
        api_col.prop(self, "api_url")
        
        # Batch Processing Settings
        batch_box = layout.box()
        batch_box.label(text="Batch Processing", icon='SEQUENCE')
        batch_col = batch_box.column()
        batch_col.prop(self, "use_batch_processing")
        
        # Batch size setting은 batch processing이 활성화된 경우에만 표시
        if self.use_batch_processing:
            sub_col = batch_col.column()
            sub_col.prop(self, "batch_size")
            # 배치 처리 관련 안내 메시지 추가
            sub_col.label(text="Smaller batch sizes are more reliable but take longer", icon='INFO')

        # Logging Settings
        log_box = layout.box()
        log_box.label(text="Logging Configuration", icon='TEXT')
        log_col = log_box.column()
        log_col.prop(self, "debug_level")
        log_col.prop(self, "log_to_file")
        
        if self.log_to_file:
            sub_col = log_col.column()
            sub_col.prop(self, "log_path")
        
        # Response Settings
        response_box = layout.box()
        response_box.label(text="Response Management", icon='FILE_TEXT')
        response_col = response_box.column()
        response_col.prop(self, "save_response")
        
        if self.save_response:
            response_col.prop(self, "response_path")

    def get_log_path(self):
        """Generate the current log file path with timestamp"""
        if not self.log_to_file or not self.log_path:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path(self.log_path)
        return str(log_dir / f"ai_organizer_{timestamp}.log")

    def get_response_path(self):
        """Generate the response file path with timestamp"""
        if not self.save_response or not self.response_path:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response_dir = Path(self.response_path)
        return str(response_dir / f"ai_response_{timestamp}.json")

    def validate_paths(self):
        """Validate and create necessary directories"""
        try:
            if self.log_to_file:
                log_dir = Path(self.log_path)
                log_dir.mkdir(parents=True, exist_ok=True)
                
            if self.save_response:
                response_dir = Path(self.response_path)
                response_dir.mkdir(parents=True, exist_ok=True)
                
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create directories: {str(e)}")
            return False

def get_prefs():
    """Utility function to get addon preferences"""
    addon_prefs = bpy.context.preferences.addons.get("ai_organizer")
    if addon_prefs:
        return addon_prefs.preferences
    return None