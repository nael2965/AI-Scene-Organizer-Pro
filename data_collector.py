# ai_organizer/data_collector.py
import bpy
import base64
import struct
from .utils import get_geometry_hash, logger
import json
try:
    import bpy  # type: ignore
except ImportError:
    pass

class SceneDataCollector:
    def __init__(self):
        self.geometry_database = {}
        self.light_database = {}
        self.camera_database = {}
        self.objects_data = []
        self.progress = 0
        self.total_objects = 0

    def collect_geometry_data(self, mesh, context):
        """순수 지오메트리 데이터 수집"""
        try:
            logger.info(f"Collecting geometry data for mesh: {mesh.name}")
            vertices = []
            for v in mesh.vertices:
                vertices.extend([v.co.x, v.co.y, v.co.z])

            faces = []
            for poly in mesh.polygons:
                if len(poly.vertices) == 3:
                    faces.extend(poly.vertices)
                else:
                    for i in range(1, len(poly.vertices) - 1):
                        faces.extend([poly.vertices[0], poly.vertices[i], poly.vertices[i + 1]])

            vertex_bytes = struct.pack(f'{len(vertices)}f', *vertices)
            face_bytes = struct.pack(f'{len(faces)}i', *faces)
            
            # 바운딩 박스 계산
            bbox_min = [float('inf')] * 3
            bbox_max = [float('-inf')] * 3
            
            for v in mesh.vertices:
                for i in range(3):
                    bbox_min[i] = min(bbox_min[i], v.co[i])
                    bbox_max[i] = max(bbox_max[i], v.co[i])
            
            dimensions = [bbox_max[i] - bbox_min[i] for i in range(3)]
            volume = dimensions[0] * dimensions[1] * dimensions[2]
            
            geo_data = {
                "vertex_data": base64.b64encode(vertex_bytes).decode('utf-8'),
                "face_data": base64.b64encode(face_bytes).decode('utf-8'),
                "vertex_count": len(mesh.vertices),
                "face_count": len(mesh.polygons),
                "bounds": {
                    "dimensions": dimensions,
                    "volume": volume,
                    "bbox_min": bbox_min,
                    "bbox_max": bbox_max
                }
            }
            logger.debug(f"Geometry data collected: {geo_data}")
            return geo_data

        except Exception as e:
            logger.error(f"Error collecting geometry data for mesh {mesh.name}: {e}", exc_info=True)
            return None


    def collect_scene_data(self, context):
        """씬의 모든 데이터 수집"""
        try:
            logger.info("Starting scene data collection.")
            self.total_objects = len(context.scene.objects)
            self.progress = 0
            
            for i, obj in enumerate(context.scene.objects):
                base_data = {
                    "name": obj.name,
                    "type": obj.type,
                    "transform": {
                        "location": list(obj.location),
                        "rotation": list(obj.rotation_euler),
                        "scale": list(obj.scale)
                    },
                    "parent": obj.parent.name if obj.parent else None,
                    "children": [child.name for child in obj.children],
                    "modifiers": [mod.name for mod in obj.modifiers]
                }

                if obj.type == 'MESH' and obj.data:
                    mesh = obj.data
                    geo_hash = get_geometry_hash(mesh)
                    
                    if geo_hash not in self.geometry_database:
                        geo_data = self.collect_geometry_data(mesh, context)
                        if geo_data:
                            self.geometry_database[geo_hash] = geo_data
                    
                    base_data.update({
                        "geometry_hash": geo_hash,
                        "data_name": mesh.name,
                        "materials": [mat.material.name if mat.material else "" for mat in obj.material_slots],
                        "dimensions": list(obj.dimensions),
                        "bounds_type": obj.display_bounds_type
                    })
                    
                elif obj.type == 'LIGHT' and obj.data:
                    light = obj.data
                    light_hash = hash(f"{light.type}_{tuple(light.color)}_{light.energy}")
                    
                    if light_hash not in self.light_database:
                        self.light_database[light_hash] = {
                            "type": light.type,
                            "color": list(light.color),
                            "energy": light.energy,
                            "size": getattr(light, 'size', 0) if hasattr(light, 'size') else 0,
                            "shadow_soft_size": getattr(light, 'shadow_soft_size', 0) if hasattr(light, 'shadow_soft_size') else 0,
                            "use_contact_shadows": getattr(light, 'use_contact_shadows', False) if hasattr(light, 'use_contact_shadows') else False
                        }
                    
                    base_data.update({
                        "light_hash": light_hash,
                        "data_name": light.name
                    })
                    
                elif obj.type == 'CAMERA' and obj.data:
                    camera = obj.data
                    camera_hash = hash(f"{camera.type}_{camera.lens}_{camera.sensor_width}")
                    
                    if camera_hash not in self.camera_database:
                        self.camera_database[camera_hash] = {
                            "type": camera.type,
                            "lens": camera.lens,
                            "sensor_width": camera.sensor_width,
                            "dof": {
                                "use_dof": camera.dof.use_dof,
                                "focus_distance": camera.dof.focus_distance
                            } if hasattr(camera, 'dof') else {"use_dof": False, "focus_distance": 0},
                            "clip_start": camera.clip_start,
                            "clip_end": camera.clip_end
                        }
                    
                    base_data.update({
                        "camera_hash": camera_hash,
                        "data_name": camera.name
                    })
                
                self.objects_data.append(base_data)
                self.progress = int(((i + 1) / self.total_objects) * 100)
                from .utils import update_progress
                update_progress(context, self.progress)
            
            scene_data = {
                "geometry_database": self.geometry_database,
                "light_database": self.light_database,
                "camera_database": self.camera_database,
                "objects": self.objects_data,
                "scene_info": {
                    "name": context.scene.name,
                    "render_engine": context.scene.render.engine,
                    "unit_settings": {
                        "system": context.scene.unit_settings.system,
                        "scale_length": context.scene.unit_settings.scale_length
                    }
                }
            }
            logger.info("Scene data collection completed.")
            logger.debug(f"Collected scene data: {json.dumps(scene_data, indent=2)}")
            return scene_data
            
        except Exception as e:
            logger.error(f"Error collecting scene data: {e}", exc_info=True)
            return None