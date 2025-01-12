# ai_organizer/utils.py
import bpy
import base64
import struct
import logging

logger = logging.getLogger(__name__)

def get_geometry_hash(mesh):
    """메시의 고유 해시값 생성"""
    vertex_data = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]
    face_data = [tuple(p.vertices) for p in mesh.polygons]
    return hash(str(vertex_data) + str(face_data))

def create_default_hierarchy():
    """기본 계층 구조 생성"""
    return {
        "collection_hierarchy": {
            "name": "Scene Organization",
            "children": [
                {
                    "name": "Meshes",
                    "description": "All mesh objects",
                    "objects": [obj.name for obj in bpy.data.objects if obj.type == 'MESH'],
                    "children": []
                },
                {
                    "name": "Lights",
                    "description": "All light sources",
                    "objects": [obj.name for obj in bpy.data.objects if obj.type == 'LIGHT'],
                    "children": []
                },
                {
                    "name": "Cameras",
                    "description": "All cameras",
                    "objects": [obj.name for obj in bpy.data.objects if obj.type == 'CAMERA'],
                    "children": []
                },
                {
                    "name": "Other",
                    "description": "Other objects",
                    "objects": [obj.name for obj in bpy.data.objects if obj.type not in {'MESH', 'LIGHT', 'CAMERA'}],
                    "children": []
                }
            ]
        },
        "object_metadata": {}
    }
    
def balance_braces(s):
    # 중괄호 균형 맞추기
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
            # 닫는 중괄호가 더 많은 경우 무시
        else:
            result.append(char)
    
    # 남은 여는 중괄호 처리
    result.extend('}' * len(stack))
    
    return ''.join(result)

def clean_json_str(s):
    s = s.replace(',}', '}')
    s = s.replace(',]', ']')
    s = s.replace('}}', '} }')
    s = s.replace(']}', '] }')
    s = s.replace('"{', '\" {')
    s = s.replace('}"', '} \"')
    # 쉼표 누락된 경우 추가
    s = s.replace('}{', '},{')
    return s
    
def create_collection_hierarchy(context, hierarchy):
    """컬렉션 계층 구조 생성"""
    root_collection = bpy.data.collections.new(hierarchy["name"])
    context.scene.collection.children.link(root_collection)
    _create_subcollections(root_collection, hierarchy["children"])
    return root_collection

def _create_subcollections(parent_collection, children):
    """하위 컬렉션 생성"""
    for child in children:
        sub_collection = bpy.data.collections.new(child["name"])
        parent_collection.children.link(sub_collection)
        _create_subcollections(sub_collection, child.get("children", []))
        
def update_progress(context, progress):
    """상태 표시줄 업데이트"""
    context.scene.ai_organizer_progress = progress