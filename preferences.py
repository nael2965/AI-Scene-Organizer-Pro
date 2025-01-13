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
        description="AI API authentication key",
        default="",
        subtype='PASSWORD'
    )

    # 통합된 모델 선택 드롭다운
    ai_model: EnumProperty(
        name="AI Model",
        description="Select AI model to use for scene organization", # 툴팁은 영어로
        items=[
            # Gemini Models
            ('gemini-2.0-flash-exp', "Gemini 2.0 Flash (Experimental)", "Latest experimental version of Gemini 2.0"),
            ('gemini-1.5-flash-latest', "Gemini 1.5 Flash (Latest)", "Latest development version of Gemini 1.5 Flash"),
            ('gemini-1.5-flash', "Gemini 1.5 Flash (Stable)", "Latest stable version of Gemini 1.5 Flash"),
            ('gemini-1.5-flash-001', "Gemini 1.5 Flash 001", "Public release version 001 of Gemini 1.5 Flash"),
            ('gemini-1.5-flash-002', "Gemini 1.5 Flash 002", "Public release version 002 of Gemini 1.5 Flash"),
            ('gemini-1.5-flash-8b-latest', "Gemini 1.5 Flash 8B (Latest)", "Latest 8B development version"),
            ('gemini-1.5-flash-8b', "Gemini 1.5 Flash 8B (Stable)", "Latest stable 8B version"),
            ('gemini-1.5-flash-8b-001', "Gemini 1.5 Flash 8B 001", "Public release 8B version 001"),
            ('gemini-1.5-pro-latest', "Gemini 1.5 Pro (Latest)", "Latest Pro development version"),
            ('gemini-1.5-pro', "Gemini 1.5 Pro (Stable)", "Latest stable Pro version"),
            ('gemini-1.5-pro-001', "Gemini 1.5 Pro 001", "Public release Pro version 001"),
            ('gemini-1.5-pro-002', "Gemini 1.5 Pro 002", "Public release Pro version 002"),
            
            # Claude Models (준비중)
            ('claude-placeholder', "Claude (Preparing)", "Claude models are not yet available"),
            
            # GPT Models (준비중)
            ('gpt-placeholder', "GPT (Preparing)", "GPT models are not yet available"),
        ],
        default='gemini-1.5-flash'
    )

    @property
    def api_url(self):
        """선택된 모델에 따른 동적 API URL 생성"""
        # HEADER나 준비중인 모델은 제외
        if self.ai_model.startswith('gemini-'):
            base_url = "https://generativelanguage.googleapis.com/v1beta/models"
            return f"{base_url}/{self.ai_model}:generateContent"
        return ""
    
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
        
        # AI 모델 설정
        model_box = layout.box()
        model_box.label(text="AI Model Settings", icon='RNA')
        model_box.prop(self, "ai_model")
        model_box.prop(self, "api_key")
        
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
            sub_col.label(text="Larger batch sizes are more reliable but more possible to be over the token limit", icon='INFO')

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