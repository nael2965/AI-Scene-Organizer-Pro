import bpy
import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path

# 라이브러리 경로 설정
here = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(here, 'lib')
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

# 애드온 모듈 임포트
from .ai_operator import AISceneOrganizerOperator
from .preferences import AISceneOrganizerPreferences
from .utils import logger, setup_logging
from .ui import menu_func, draw_progress_bar, register_properties, unregister_properties

bl_info = {
    "name": "AI Scene Organizer Pro",
    "blender": (4, 3, 2),
    "category": "Object",
    "version": (1, 8, 1),
    "author": "Nael",
    "description": "Advanced AI-powered scene organization system with hierarchical analysis",
    "location": "View3D > Object Menu > AI Scene Organizer",
    "doc_url": "",
    "tracker_url": "",
    "warning": ""
}

def initialize_logging(preferences):
    """로깅 시스템 초기화"""
    try:
        setup_logging(preferences)
        logger.info(f"AI Scene Organizer {'.'.join(map(str, bl_info['version']))} initialization started")
        return True
    except Exception as e:
        print(f"Error initializing logging system: {e}")
        return False

def initialize_workspace(preferences):
    """작업 디렉토리 설정"""
    try:
        if preferences.log_to_file and preferences.log_path:
            Path(preferences.log_path).mkdir(parents=True, exist_ok=True)
            
        if preferences.save_response and preferences.response_path:
            Path(preferences.response_path).mkdir(parents=True, exist_ok=True)
            
        return True
    except Exception as e:
        print(f"Workspace initialization failed: {e}")
        return False

def validate_environment():
    """운영 환경과 종속성 검증"""
    try:
        # Blender 버전 확인
        version = bpy.app.version
        if version < bl_info["blender"]:
            raise Exception(f"Requires Blender {'.'.join(map(str, bl_info['blender']))} or newer")

        # 라이브러리 임포트 검증
        required_modules = {
            'aiohttp': 'HTTP client library',
            'multidict': 'Dictionary with multiple values per key',
            'yarl': 'URL parsing library',
            'attrs': 'Classes without boilerplate',
            'async_timeout': 'Timeout context manager'
        }

        missing_modules = []
        for module_name, description in required_modules.items():
            try:
                __import__(module_name)
            except ImportError as e:
                missing_modules.append(f"{module_name} ({description})")

        if missing_modules:
            raise Exception("Missing required modules: " + ", ".join(missing_modules))

        logger.info("Environment validation successful")
        return True

    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        raise

def write_startup_log():
    """시작 정보 로깅"""
    try:
        logger.info("=== AI Scene Organizer Startup Information ===")
        logger.info(f"Version: {'.'.join(map(str, bl_info['version']))}")
        logger.info(f"Blender Version: {'.'.join(map(str, bpy.app.version))}")
        logger.info(f"Python Version: {sys.version}")
        logger.info(f"Library Path: {lib_dir}")
        logger.info("=========================================")
    except Exception as e:
        logger.error(f"Failed to write startup log: {e}")

def register():
    """애드온 등록"""
    try:
        # 환경 검증
        validate_environment()
        
        # 클래스 등록
        bpy.utils.register_class(AISceneOrganizerPreferences)
        bpy.utils.register_class(AISceneOrganizerOperator)
        
        # UI와 프로퍼티 등록
        register_properties()
        bpy.types.VIEW3D_MT_object.append(menu_func)
        
        # 설정이 있다면 초기화 진행
        addon_prefs = bpy.context.preferences.addons.get("ai_organizer")
        if addon_prefs:
            if initialize_workspace(addon_prefs.preferences):
                setup_logging(addon_prefs.preferences)
                write_startup_log()
        
        logger.info("AI Scene Organizer Pro successfully registered")
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        if 'addon_prefs' in locals():
            try:
                unregister()
            except:
                pass
        raise

def unregister():
    """애드온 등록 해제"""
    try:
        logger.info("Starting addon unregistration")
        
        # UI 요소 제거
        bpy.types.VIEW3D_MT_object.remove(menu_func)
        unregister_properties()
        
        # 클래스 등록 해제
        bpy.utils.unregister_class(AISceneOrganizerOperator)
        
        # 로깅 정리
        for handler in logger._logger.handlers[:]:
            logger._logger.removeHandler(handler)
        
        # 설정 클래스 등록 해제
        bpy.utils.unregister_class(AISceneOrganizerPreferences)
        
        logger.info("AI Scene Organizer successfully unregistered")
        
    except Exception as e:
        print(f"Error during unregistration: {e}")
        raise

if __name__ == "__main__":
    register()