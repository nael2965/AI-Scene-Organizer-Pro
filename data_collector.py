import bpy
import base64
import struct
from .utils import get_geometry_hash, logger

class SceneDataCollector:
    def __init__(self):
        self.geometry_database = {}
        self.light_database = {}
        self.camera_database = {}
        self.objects_data = []

    def collect_geometry_data(self, mesh):
        """순수 지오메트리 데이터 수집"""
        try:
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

            # 바이너리 데이터를 base64로 인코딩
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

            return {
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
        except Exception as e:
            logger.error(f"Error collecting geometry data: {e}", exc_info=True)
            return None

    def collect_light_data(self, light):
        """라이트 데이터 수집"""
        try:
            return {
                "type": light.type,
                "color": list(light.color),
                "energy": light.energy,
                "shadow_soft_size": getattr(light, 'shadow_soft_size', 0),
                "use_nodes": light.use_nodes,
                "spot_size": getattr(light, 'spot_size', 0),
                "spot_blend": getattr(light, 'spot_blend', 0),
                "use_shadow": light.use_shadow,
                "falloff_type": getattr(light, 'falloff_type', 'INVERSE_SQUARE')
            }
        except Exception as e:
            logger.error(f"Error collecting light data: {e}", exc_info=True)
            return None

    def collect_camera_data(self, camera):
        """카메라 데이터 수집"""
        try:
            return {
                "type": camera.type,
                "lens": camera.lens,
                "sensor_width": camera.sensor_width,
                "sensor_height": camera.sensor_height,
                "sensor_fit": camera.sensor_fit,
                "dof": {
                    "use_dof": camera.dof.use_dof,
                    "focus_distance": camera.dof.focus_distance,
                    "aperture_fstop": camera.dof.aperture_fstop
                },
                "shift_x": camera.shift_x,
                "shift_y": camera.shift_y,
                "clip_start": camera.clip_start,
                "clip_end": camera.clip_end,
                "ortho_scale": getattr(camera, 'ortho_scale', 0) if camera.type == 'ORTHO' else None
            }
        except Exception as e:
            logger.error(f"Error collecting camera data: {e}", exc_info=True)
            return None

    def collect_scene_data(self, context):
        """씬의 모든 데이터 수집"""
        try:
            logger.info("Starting scene data collection")
            
            for obj in context.scene.objects:
                # 기본 오브젝트 데이터 수집
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
                    "collection_hierarchy": [c.name for c in obj.users_collection],
                    "hide_viewport": obj.hide_viewport,
                    "hide_render": obj.hide_render
                }

                # 타입별 특수 데이터 수집
                if obj.type == 'MESH' and obj.data:
                    mesh = obj.data
                    geo_hash = get_geometry_hash(mesh)
                    
                    if geo_hash not in self.geometry_database:
                        geo_data = self.collect_geometry_data(mesh)
                        if geo_data:
                            self.geometry_database[geo_hash] = geo_data

                    base_data.update({
                        "geometry_hash": geo_hash,
                        "modifiers": [
                            {
                                "name": mod.name,
                                "type": mod.type,
                                "show_viewport": mod.show_viewport,
                                "show_render": mod.show_render
                            } for mod in obj.modifiers
                        ]
                    })

                elif obj.type == 'LIGHT' and obj.data:
                    light = obj.data
                    light_data = self.collect_light_data(light)
                    if light_data:
                        self.light_database[obj.name] = light_data
                    base_data["light_data_name"] = obj.name

                elif obj.type == 'CAMERA' and obj.data:
                    camera = obj.data
                    camera_data = self.collect_camera_data(camera)
                    if camera_data:
                        self.camera_database[obj.name] = camera_data
                    base_data["camera_data_name"] = obj.name

                self.objects_data.append(base_data)

            # 전체 씬 데이터 구성
            scene_data = {
                "geometry_database": self.geometry_database,
                "light_database": self.light_database,
                "camera_database": self.camera_database,
                "objects": self.objects_data,
                "scene_info": {
                    "name": context.scene.name,
                    "render_engine": context.scene.render.engine,
                    "frame_current": context.scene.frame_current,
                    "frame_start": context.scene.frame_start,
                    "frame_end": context.scene.frame_end
                }
            }

            logger.info("Scene data collection completed")
            return scene_data

        except Exception as e:
            logger.error(f"Error collecting scene data: {e}", exc_info=True)
            return None