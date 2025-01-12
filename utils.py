import bpy
import base64
import struct
import logging
import os
from pathlib import Path
from datetime import datetime

# 기본 유틸리티 함수들
def get_geometry_hash(mesh):
    """Generate unique hash for mesh geometry"""
    try:
        vertex_data = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]
        face_data = [tuple(p.vertices) for p in mesh.polygons]
        return hash(str(vertex_data) + str(face_data))
    except Exception as e:
        logger.error(f"Error generating geometry hash: {e}")
        return None

def create_default_hierarchy():
    """Create default collection hierarchy"""
    return {
        "collection_hierarchy": {
            "name": "Scene",
            "type": "root",
            "description": "Default scene organization",
            "children": [
                {
                    "name": "Sets",
                    "type": "category",
                    "description": "Scene environment and structure",
                    "children": []
                },
                {
                    "name": "Staging",
                    "type": "category",
                    "description": "Scene props and elements",
                    "children": []
                },
                {
                    "name": "Lighting",
                    "type": "category",
                    "description": "Scene illumination",
                    "children": []
                },
                {
                    "name": "Cameras",
                    "type": "category",
                    "description": "Scene visualization",
                    "children": []
                }
            ]
        }
    }

def clean_json_str(s):
    """Clean and format JSON string"""
    s = s.replace(',}', '}')
    s = s.replace(',]', ']')
    s = s.replace('}}', '} }')
    s = s.replace(']}', '] }')
    s = s.replace('"{', '\" {')
    s = s.replace('}"', '} \"')
    s = s.replace('}{', '},{')
    return s

def balance_braces(s):
    """Ensure JSON string has balanced braces"""
    stack = []
    result = []
    
    for char in s:
        if char == '{':
            stack.append(char)
            result.append(char)
        elif char == '}':
            if stack and stack[-1] == '{':
                stack.pop()
                result.append(char)
        else:
            result.append(char)
    
    result.extend('}' * len(stack))
    return ''.join(result)

# 지오메트리 처리 유틸리티
def encode_geometry_data(mesh):
    """Encode mesh geometry data to Base64"""
    try:
        vertices = []
        for v in mesh.vertices:
            vertices.extend([v.co.x, v.co.y, v.co.z])

        faces = []
        for poly in mesh.polygons:
            faces.extend(poly.vertices)

        vertex_bytes = struct.pack(f'{len(vertices)}f', *vertices)
        face_bytes = struct.pack(f'{len(faces)}i', *faces)
        
        return {
            "vertex_data": base64.b64encode(vertex_bytes).decode('utf-8'),
            "face_data": base64.b64encode(face_bytes).decode('utf-8')
        }
    except Exception as e:
        logger.error(f"Error encoding geometry data: {e}")
        return None

def calculate_bounds(mesh):
    """Calculate mesh boundary information"""
    try:
        bbox_min = [float('inf')] * 3
        bbox_max = [float('-inf')] * 3
        
        for v in mesh.vertices:
            for i in range(3):
                bbox_min[i] = min(bbox_min[i], v.co[i])
                bbox_max[i] = max(bbox_max[i], v.co[i])
        
        dimensions = [bbox_max[i] - bbox_min[i] for i in range(3)]
        volume = dimensions[0] * dimensions[1] * dimensions[2]
        
        return {
            "dimensions": dimensions,
            "volume": volume,
            "bbox_min": bbox_min,
            "bbox_max": bbox_max
        }
    except Exception as e:
        logger.error(f"Error calculating bounds: {e}")
        return None

# 컬렉션 관리 유틸리티
def validate_collection_name(name):
    """Validate and clean collection names"""
    valid_name = "".join(c for c in name if c.isalnum() or c in "._-")
    return valid_name or "Collection"

def create_collection_hierarchy(context, hierarchy):
    """Create collection hierarchy in Blender"""
    root_collection = bpy.data.collections.new(hierarchy["name"])
    context.scene.collection.children.link(root_collection)
    _create_subcollections(root_collection, hierarchy.get("children", []))
    return root_collection

def _create_subcollections(parent_collection, children):
    """Create subcollections recursively"""
    for child in children:
        sub_collection = bpy.data.collections.new(child["name"])
        parent_collection.children.link(sub_collection)
        _create_subcollections(sub_collection, child.get("children", []))

# 로깅 시스템
logger = logging.getLogger('AISceneOrganizer')
logger.setLevel(logging.DEBUG)

def setup_logging(preferences):
    """Configure logging system with file output"""
    logger = logging.getLogger('AISceneOrganizer')
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 로그 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, preferences.debug_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 설정
    if preferences.log_to_file:
        try:
            log_path = preferences.get_log_path()
            if log_path:
                # 로그 디렉토리 생성
                Path(log_path).parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(
                    log_path,
                    encoding='utf-8',
                    mode='a'
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                logger.info(f"Log file initialized at: {log_path}")
        except Exception as e:
            logger.error(f"Failed to initialize log file: {e}")
            
    return logger

# 진행 상태 관리
def update_progress(context, progress):
    """Update progress bar in Blender UI"""
    try:
        context.scene.ai_organizer_progress = int(progress)
    except Exception as e:
        logger.error(f"Progress update error: {e}")

def get_scene_stats():
    """Collect scene statistics"""
    try:
        return {
            "object_count": len(bpy.data.objects),
            "collection_count": len(bpy.data.collections),
            "mesh_count": len(bpy.data.meshes),
            "light_count": len(bpy.data.lights),
            "camera_count": len(bpy.data.cameras),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error collecting scene stats: {e}")
        return None