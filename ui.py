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
        
def register_properties():
    # Scene properties for API settings
    bpy.types.Scene.ai_organizer_api_key = bpy.props.StringProperty(
        name="API Key",
        description="Enter your Google Gemini API key",
        default=""
    )
    
    bpy.types.Scene.ai_organizer_api_url = bpy.props.StringProperty(
        name="API URL",
        description="Enter your Google Gemini API URL",
        default="https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    )
    
    # Progress bar property
    bpy.types.Scene.ai_organizer_progress = bpy.props.IntProperty(
        name="AI Organizer Progress",
        description="AI Organizer progress percentage",
        default=0,
        min=0,
        max=100
    )

def unregister_properties():
    del bpy.types.Scene.ai_organizer_api_key
    del bpy.types.Scene.ai_organizer_api_url
    del bpy.types.Scene.ai_organizer_progress
    
def setup_logging():
    try:
        # Scene properties를 사용
        scene = bpy.context.scene
        log_level = getattr(logging, scene.ai_organizer_debug_level)
        
        # 기본 로깅 설정
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 전역 logger 설정
        global logger
        logger = logging.getLogger(__name__)
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # 기본값으로 fallback
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)